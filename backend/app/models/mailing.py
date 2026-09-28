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
"""

from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Text,
                        Boolean, Index)
from sqlalchemy.orm import relationship

from app.database import Base


class MailCampaign(Base):
    """Un message envoyé à un groupe d'adhérents."""
    __tablename__ = "mail_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)          # texte saisi par l'expéditeur
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

    campaign = relationship("MailCampaign", back_populates="attachments")


Index("ix_mail_recipients_campagne_ouverture",
      MailRecipient.campaign_id, MailRecipient.first_opened_at)
