"""Mise en forme des courriels : désinfection du HTML et rendu.

Le corps d'un message est saisi dans un éditeur enrichi. Ce qui en sort est
du HTML fourni par un navigateur : il ne faut jamais le réémettre tel quel,
ni dans un courriel, ni dans l'aperçu affiché dans l'application. On le
repasse donc par une liste blanche stricte (« nh3 », le même moteur que
celui de Firefox) plutôt que par une expression régulière maison — un
désinfecteur écrit à la main est un piège classique.
"""

import re
from html import escape

import nh3

# Volontairement pauvre : ce qui traverse toutes les messageries. Les tableaux,
# les styles et les images distantes sont exclus — ils s'affichent mal ailleurs
# que dans le navigateur où le message a été écrit.
BALISES = {
    "p", "br", "b", "strong", "i", "em", "u", "s",
    "ul", "ol", "li", "blockquote", "h2", "h3", "a", "div", "span",
}
ATTRIBUTS = {"a": {"href", "title"}}
PROTOCOLES = {"http", "https", "mailto", "tel"}


def nettoyer(html: str) -> str:
    """HTML réduit à ce qui est sûr et lisible partout."""
    return nh3.clean(
        html or "",
        tags=BALISES,
        attributes=ATTRIBUTS,
        url_schemes=PROTOCOLES,
        link_rel="noopener noreferrer",
    )


_BLOCS_FERMANTS = re.compile(r"</(p|div|h2|h3|li|blockquote|ul|ol)>", re.I)
_SAUTS = re.compile(r"<br\s*/?>", re.I)
_BALISE = re.compile(r"<[^>]+>")


def en_texte(html: str) -> str:
    """Version texte seul, pour la partie « text/plain » du message.

    Un courriel sans partie texte est plus souvent classé indésirable, et
    reste illisible pour qui lit en texte brut. On reconstitue donc les
    retours à la ligne à partir des balises de bloc plutôt que de tout
    aplatir en une seule ligne.
    """
    t = _SAUTS.sub("\n", html or "")
    t = _BLOCS_FERMANTS.sub("\n", t)
    t = _BALISE.sub("", t)
    from html import unescape
    t = unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def depuis_texte(texte: str) -> str:
    """HTML d'un corps saisi en texte simple (campagnes d'avant l'éditeur).

    Les anciennes campagnes n'ont que du texte : une ligne vide y sépare deux
    paragraphes. Sans cette conversion, elles s'afficheraient d'un bloc.
    """
    morceaux = [p.strip() for p in re.split(r"\n\s*\n", texte or "") if p.strip()]
    return "".join(f"<p>{escape(p).replace(chr(10), '<br>')}</p>" for p in morceaux)
