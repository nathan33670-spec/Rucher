"""Réponses d'erreur explicites et journalisées.

Sans ces gestionnaires, une exception non prévue renvoyait le texte brut
« Internal Server Error » : l'interface affichait « Erreur » et personne — ni
l'utilisateur ni l'administrateur — ne pouvait savoir ce qui s'était passé.

Chaque erreur inattendue reçoit désormais une **référence courte** renvoyée à
l'utilisateur et écrite dans les logs à côté de la trace complète : il suffit
de la citer pour retrouver la cause exacte dans `docker compose logs backend`.
"""

import traceback
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Libellés lisibles pour les champs les plus courants ; à défaut on affiche le
# nom technique, ce qui reste plus utile qu'un message générique.
FIELD_LABELS = {
    "name": "Nom", "title": "Titre", "email": "Identifiant",
    "password": "Mot de passe", "new_password": "Nouveau mot de passe",
    "current_password": "Mot de passe actuel",
    "quantity": "Quantité", "quantity_kg": "Quantité (kg)",
    "amount": "Montant", "unit_price": "Prix unitaire",
    "harvest_date": "Date de récolte", "visited_at": "Date de visite",
    "start_at": "Début", "end_at": "Fin", "date": "Date",
    "application_date": "Date d'application",
    "hive_id": "Ruche", "apiary_id": "Rucher", "category_id": "Catégorie",
    "jar_id": "Pot", "harvest_id": "Récolte", "role": "Rôle",
    "comment": "Commentaire", "message": "Message",
    "jar_weight_g": "Format du pot", "owner_user_id": "Propriétaire",
}

# Messages Pydantic traduits ; les autres types sont repris tels quels.
TYPE_MESSAGES = {
    "missing": "à renseigner",
    "string_too_short": "à renseigner",
    "int_parsing": "doit être un nombre entier",
    "float_parsing": "doit être un nombre",
    "int_type": "doit être un nombre entier",
    "float_type": "doit être un nombre",
    "bool_parsing": "doit être vrai ou faux",
    "datetime_parsing": "date invalide",
    "datetime_from_date_parsing": "date invalide",
    "date_parsing": "date invalide",
    "enum": "valeur non autorisée",
    "greater_than_equal": "valeur trop petite",
    "less_than_equal": "valeur trop grande",
}


def _label(loc) -> str:
    """Dernier segment nommé du chemin d'erreur, en libellé lisible."""
    parts = [p for p in loc if isinstance(p, str) and p not in ("body", "query", "path")]
    if not parts:
        return "Formulaire"
    return FIELD_LABELS.get(parts[-1], parts[-1].replace("_", " ").capitalize())


def format_validation_error(exc: RequestValidationError) -> str:
    """« Quantité (kg) : à renseigner · Date de récolte : date invalide »."""
    seen, messages = set(), []
    for err in exc.errors():
        label = _label(err.get("loc", ()))
        detail = TYPE_MESSAGES.get(err.get("type"), err.get("msg", "valeur invalide"))
        line = f"{label} : {detail}"
        if line not in seen:
            seen.add(line)
            messages.append(line)
    if not messages:
        return "Saisie invalide."
    return "Saisie incomplète — " + " · ".join(messages[:4])


def _integrity_message(exc: IntegrityError) -> tuple[int, str]:
    """Traduit les violations de contraintes en message compréhensible."""
    text = str(getattr(exc, "orig", exc))
    low = text.lower()
    if "unique" in low or "duplicate key" in low:
        return 409, "Cet enregistrement existe déjà (valeur en double)."
    if "foreign key" in low:
        return 409, ("Élément lié introuvable, ou encore utilisé ailleurs : "
                     "supprimez d'abord ce qui en dépend.")
    if "not null" in low or "null value" in low:
        return 422, "Un champ obligatoire n'a pas été renseigné."
    return 409, "Enregistrement refusé par la base de données."


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": format_validation_error(exc)})

    @app.exception_handler(IntegrityError)
    async def _integrity(request: Request, exc: IntegrityError):
        status, message = _integrity_message(exc)
        ref = uuid.uuid4().hex[:6].upper()
        print(f"⚠️  [{ref}] IntegrityError sur {request.method} {request.url.path} : {exc}")
        return JSONResponse(status_code=status, content={"detail": f"{message} (réf. {ref})"})

    @app.exception_handler(SQLAlchemyError)
    async def _sqlalchemy(request: Request, exc: SQLAlchemyError):
        ref = uuid.uuid4().hex[:6].upper()
        print(f"❌ [{ref}] Erreur base de données sur {request.method} {request.url.path}")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return JSONResponse(status_code=500, content={"detail": (
            "Enregistrement impossible : la base de données a refusé l'opération "
            f"(réf. {ref}). Signalez cette référence à l'administrateur."
        )})

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        ref = uuid.uuid4().hex[:6].upper()
        print(f"❌ [{ref}] Erreur non gérée sur {request.method} {request.url.path}")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return JSONResponse(status_code=500, content={"detail": (
            f"Erreur interne du serveur (réf. {ref}). "
            "L'incident est enregistré ; signalez cette référence à l'administrateur."
        )})
