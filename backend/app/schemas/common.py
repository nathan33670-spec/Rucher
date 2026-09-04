"""Types partagés par les schémas d'entrée."""

from datetime import datetime, timezone
from typing import Annotated, Optional
from pydantic import StringConstraints, AfterValidator

# Chaîne obligatoire réellement non vide : les espaces sont retirés et une
# saisie vide est refusée. Sans cela, `str` accepte "" et l'on enregistrait
# par exemple un rucher sans nom.
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _to_naive_utc(v):
    """Ramène une date/heure à un instant UTC « naïf ».

    Le navigateur envoie des dates au format ISO terminées par « Z »
    (``2026-07-15T00:00:00.000Z``), donc porteuses d'un fuseau. Or toutes les
    colonnes DateTime du projet sont sans fuseau : PostgreSQL refusait alors
    l'insertion (« can't subtract offset-naive and offset-aware datetimes ») et
    la requête se terminait en erreur 500 — c'était le cas de la saisie d'une
    récolte de miel dès qu'une date était renseignée.

    On normalise donc une bonne fois pour toutes, à l'entrée des schémas.
    """
    if isinstance(v, datetime) and v.tzinfo is not None:
        return v.astimezone(timezone.utc).replace(tzinfo=None)
    return v


# Date/heure d'entrée : accepte une valeur avec ou sans fuseau, stocke sans.
NaiveDateTime = Annotated[datetime, AfterValidator(_to_naive_utc)]
OptNaiveDateTime = Optional[NaiveDateTime]
