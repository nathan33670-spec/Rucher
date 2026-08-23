"""Types partagés par les schémas d'entrée."""

from typing import Annotated
from pydantic import StringConstraints

# Chaîne obligatoire réellement non vide : les espaces sont retirés et une
# saisie vide est refusée. Sans cela, `str` accepte "" et l'on enregistrait
# par exemple un rucher sans nom.
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
