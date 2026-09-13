"""Attribution des numéros de ruche manquants.

Avant l'introduction du champ « numéro », une ruche sans nom s'affichait avec
son identifiant de base (« Ruche #37 ») : un numéro que personne n'a choisi,
que l'on ne peut pas modifier, et qui n'a aucun rapport avec ce qui est peint
sur la ruche.

Au démarrage, les ruches qui n'ont **ni numéro ni NAPI** reçoivent donc le
premier entier libre. Celles qui portent déjà un identifiant saisi à la main
(y compris dans l'ancien champ NAPI) ne sont pas touchées : leur affichage ne
change pas, et le choix de recopier ou non reste à l'association.
"""

from sqlalchemy import select, or_, func

from app.database import async_session
from app.models.apiary import Hive


def _blank(value) -> bool:
    return value is None or not str(value).strip()


async def assign_missing_numbers() -> int:
    """Numérote les ruches qui s'afficheraient sinon avec leur clé primaire."""
    async with async_session() as db:
        res = await db.execute(select(Hive).order_by(Hive.apiary_id, Hive.id))
        hives = list(res.scalars().all())

        used = set()
        todo = []
        for h in hives:
            if not _blank(h.number):
                try:
                    used.add(int(str(h.number).strip()))
                except ValueError:
                    pass
                continue
            if _blank(h.napi_number):
                todo.append(h)

        if not todo:
            return 0

        n = 1
        for h in todo:
            while n in used:
                n += 1
            h.number = str(n)
            used.add(n)
        await db.commit()

    print(f"✅ {len(todo)} ruche(s) numérotée(s) automatiquement")
    return len(todo)


def hive_label(hive) -> str:
    """Libellé d'une ruche, sans jamais exposer sa clé primaire.

    Ordre : le nom s'il existe, sinon le numéro choisi, sinon l'ancien champ
    NAPI (sur les bases antérieures, l'identifiant s'y trouvait).
    """
    if hive is None:
        return "Ruche"
    if not _blank(getattr(hive, "name", None)):
        return hive.name
    if not _blank(getattr(hive, "number", None)):
        return f"Ruche {str(hive.number).strip()}"
    if not _blank(getattr(hive, "napi_number", None)):
        return f"Ruche {str(hive.napi_number).strip()}"
    return "Ruche sans numéro"
