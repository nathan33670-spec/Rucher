"""Campagnes d'e-mail vers les adhérents, et suivi des ouvertures.

Le suivi repose sur une image d'un pixel, propre à chaque destinataire :
l'ouverture du message charge l'image, et le serveur en garde la trace. C'est
la méthode courante, et elle a des limites qu'il faut connaître plutôt que de
prendre ses chiffres pour argent comptant :

- la plupart des messageries **bloquent les images par défaut** : une lecture
  réelle passe alors inaperçue. Le chiffre est donc un **plancher** ;
- Apple Mail précharge les images sans que personne n'ait rien lu, ce qui
  produit à l'inverse de fausses ouvertures ;
- un message lu en texte seul ne déclenche jamais rien.

On mesure donc une tendance, pas une vérité. L'interface le dit, et le suivi
se désactive campagne par campagne.

Un second mécanisme, nettement plus fiable, complète le pixel : les liens du
message passent par une redirection propre à chaque destinataire. Un clic ne
peut pas être préchargé par erreur et ne dépend pas des images : il prouve
qu'un humain a ouvert le message et agi. Un clic vaut donc ouverture, même si
le pixel n'a jamais été chargé — c'est ce qui rattrape l'essentiel des
lectures que le pixel manque.
"""

from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Text,
                        Boolean, Index, UniqueConstraint)
from sqlalchemy.orm import relationship

from app.database import Base


class MailCampaign(Base):
    """Un message envoyé à un groupe d'adhérents."""
    __tablename__ = "mail_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)          # version texte seul, toujours remplie
    # Corps mis en forme. Vide pour les campagnes d'avant l'éditeur enrichi :
    # leur texte est alors converti à l'affichage, sans réécrire l'historique.
    body_html = Column(Text, nullable=True)
    audience = Column(String(50), nullable=False, default="all")
    # Suivi des ouvertures : décidé à l'envoi, jamais rétroactif.
    tracking = Column(Boolean, default=True, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    sent_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipients = relationship("MailRecipient", back_populates="campaign",
                              cascade="all, delete-orphan", lazy="selectin")
    attachments = relationship("MailAttachment", back_populates="campaign",
                               cascade="all, delete-orphan", lazy="selectin")
    links = relationship("MailLink", back_populates="campaign",
                         cascade="all, delete-orphan", lazy="selectin")
    poll = relationship("MailPoll", back_populates="campaign", uselist=False,
                        cascade="all, delete-orphan", lazy="selectin")


class MailRecipient(Base):
    """Un destinataire d'une campagne, et ce qu'on sait de sa lecture."""
    __tablename__ = "mail_recipients"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("mail_campaigns.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200))
    email = Column(String(255), nullable=False)
    # Jeton du pixel : tiré au hasard, il ne dit rien de l'adresse qu'il suit.
    token = Column(String(64), nullable=False, unique=True, index=True)
    sent = Column(Boolean, default=False, nullable=False)
    error = Column(String(400), nullable=True)
    first_opened_at = Column(DateTime, nullable=True)
    last_opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0, nullable=False)
    # Clics : preuve d'ouverture bien plus solide que le pixel.
    first_clicked_at = Column(DateTime, nullable=True)
    last_clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0, nullable=False)

    campaign = relationship("MailCampaign", back_populates="recipients")


class MailAttachment(Base):
    """Pièce jointe d'une campagne, conservée pour mémoire de ce qui est parti."""
    __tablename__ = "mail_attachments"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("mail_campaigns.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(120), nullable=False)
    size = Column(Integer, default=0, nullable=False)
    file_path = Column(String(500), nullable=False)
    # Fichier trop lourd pour être joint : il reste sur l'application et le
    # message ne porte qu'un lien. Au-delà d'une certaine taille, une pièce
    # jointe fait rejeter tout le message par le serveur du destinataire.
    hosted = Column(Boolean, default=False, nullable=False)
    # Jeton du lien de téléchargement : long, tiré au hasard, indevinable.
    token = Column(String(64), nullable=True, unique=True, index=True)
    expires_at = Column(DateTime, nullable=True)
    download_count = Column(Integer, default=0, nullable=False)

    campaign = relationship("MailCampaign", back_populates="attachments")


class MailLink(Base):
    """Un lien du message, suivi par redirection.

    On garde l'adresse de destination en base plutôt que dans l'URL : un lien
    de redirection qui transporte sa cible est une porte ouverte au
    détournement (« open redirect »), qu'un message d'hameçonnage utiliserait
    volontiers en se réclamant du domaine de l'association.
    """
    __tablename__ = "mail_links"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("mail_campaigns.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    position = Column(Integer, nullable=False)   # rang du lien dans le message
    url = Column(Text, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)

    campaign = relationship("MailCampaign", back_populates="links")


class MailPoll(Base):
    """Sondage attaché à une campagne : une question, des réponses possibles.

    Le vote se fait **depuis le message**, sans connexion : c'est le jeton du
    destinataire qui l'identifie. Un adhérent qui ne retrouve pas son mot de
    passe doit pouvoir répondre, sinon on ne recueille l'avis que des plus
    assidus. En contrepartie, quiconque reçoit le message transféré peut voter
    à la place de son destinataire : l'interface le dit, et c'est pourquoi ce
    dispositif convient à un sondage d'organisation, pas à une élection.
    """
    __tablename__ = "mail_polls"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("mail_campaigns.id", ondelete="CASCADE"),
                         nullable=False, unique=True, index=True)
    question = Column(String(300), nullable=False)
    # Plusieurs réponses possibles (ex. « quelles dates vous conviennent ? »).
    multiple = Column(Boolean, default=False, nullable=False)
    closes_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("MailCampaign", back_populates="poll")
    options = relationship("MailPollOption", back_populates="poll",
                           cascade="all, delete-orphan", lazy="selectin",
                           order_by="MailPollOption.position")
    votes = relationship("MailVote", back_populates="poll",
                         cascade="all, delete-orphan", lazy="selectin")


class MailPollOption(Base):
    """Une réponse possible."""
    __tablename__ = "mail_poll_options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("mail_polls.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    position = Column(Integer, nullable=False)
    label = Column(String(200), nullable=False)

    poll = relationship("MailPoll", back_populates="options")


class MailVote(Base):
    """Le choix d'un destinataire.

    Rattaché au destinataire et non à l'utilisateur : c'est le jeton du
    message qui fait foi, et un même adhérent peut figurer dans plusieurs
    campagnes.
    """
    __tablename__ = "mail_votes"
    __table_args__ = (
        UniqueConstraint("poll_id", "recipient_id", "option_id", name="uq_vote_unique"),
    )

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("mail_polls.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("mail_recipients.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    option_id = Column(Integer, ForeignKey("mail_poll_options.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    voted_at = Column(DateTime, default=datetime.utcnow)

    poll = relationship("MailPoll", back_populates="votes")


Index("ix_mail_recipients_campagne_ouverture",
      MailRecipient.campaign_id, MailRecipient.first_opened_at)
