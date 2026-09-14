"""Adresse publique de l'application.

Les e-mails (identifiants, mot de passe oublié, récapitulatif) contiennent un
lien vers l'application : il leur faut son adresse. Elle était uniquement lue
dans les réglages, si bien qu'un champ vide bloquait purement et simplement
l'envoi — alors que l'application a l'information sous la main : la requête
vient du navigateur qui est justement en train de l'afficher.

On retient donc, dans l'ordre :

1. l'adresse saisie dans les réglages, qui reste prioritaire — c'est le seul
   moyen de désigner une autre adresse que celle utilisée sur le moment ;
2. l'origine annoncée par le navigateur (« Origin », puis « Referer ») ;
3. les en-têtes posés par le proxy inverse (« X-Forwarded-Proto » / « -Host »),
   pour les envois déclenchés sans navigateur ;
4. l'adresse vue par le serveur, en dernier recours.
"""

from urllib.parse import urlsplit


def _origine(valeur: str | None) -> str:
    """Schéma + hôte d'une URL, sans chemin ni paramètres."""
    if not valeur:
        return ""
    parts = urlsplit(valeur.strip())
    if not parts.scheme or not parts.netloc:
        return ""
    return f"{parts.scheme}://{parts.netloc}"


def resolve_app_url(request, cfg: dict | None = None) -> str:
    """Adresse publique de l'application, sans barre oblique finale."""
    configuree = ((cfg or {}).get("app_base_url") or "").strip()
    if configuree:
        return configuree.rstrip("/")

    if request is None:
        return ""

    entetes = request.headers

    depuis_navigateur = _origine(entetes.get("origin")) or _origine(entetes.get("referer"))
    if depuis_navigateur:
        return depuis_navigateur

    hote = entetes.get("x-forwarded-host") or entetes.get("host")
    if hote:
        schema = (entetes.get("x-forwarded-proto") or request.url.scheme or "https").split(",")[0].strip()
        return f"{schema}://{hote.split(',')[0].strip()}"

    return str(request.base_url).rstrip("/")
