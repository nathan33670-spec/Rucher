"""Numéro de ruche : attribution des manquants et libellé.

Le numéro est l'**identité** d'une ruche : c'est ce qui est peint sur la
caisse, ce qu'on annonce au rucher, ce qu'on cherche dans un historique. Il
doit donc être affiché partout et modifiable à tout moment.

Deux corrections sont réunies ici :

- **toute** ruche reçoit un numéro au démarrage. Auparavant celles qui
  portaient un NAPI étaient laissées de côté : elles s'affichaient avec ce
  NAPI, et changer leur « N° de ruche » ne changeait rien à l'écran ;
- le libellé mène par le numéro, le nom n'étant qu'un complément. Le nom
  passait avant, si bien qu'une ruche nommée ignorait complètement son
  numéro — modifier celui-ci restait sans effet visible.
"""

from sqlalchemy import select

from app.database import async_session
from app.models.apiary import Hive


def _blank(value) -> bool:
    return value is None or not str(value).strip()


def _clean(value) -> str:
    return str(value).strip()


async def assign_missing_numbers() -> int:
    """Donne un numéro modifiable à toute ruche qui n'en a pas.

    Deux cas, dans cet ordre :

    1. la ruche n'a qu'un NAPI, et ce NAPI **ne sert qu'à elle** : les bases
       antérieures y rangeaient l'identifiant de la ruche, on le reprend donc
       tel quel — le numéro affiché ne change pas, il devient simplement
       modifiable ;
    2. sinon (aucun identifiant, ou NAPI partagé avec d'autres ruches, donc
       véritable numéro d'apiculteur), la ruche reçoit le premier entier
       libre.

    Idempotent : seules les ruches sans numéro sont touchées.
    """
    async with async_session() as db:
        res = await db.execute(select(Hive).order_by(Hive.apiary_id, Hive.id))
        hives = list(res.scalars().all())

        # Numéros déjà pris, pour ne jamais créer de doublon.
        pris: set[str] = {
            _clean(h.number).lower() for h in hives if not _blank(h.number)
        }
        entiers: set[int] = set()
        for h in hives:
            if _blank(h.number):
                continue
            try:
                entiers.add(int(_clean(h.number)))
            except ValueError:
                continue

        # Un NAPI porté par plusieurs ruches est un vrai numéro d'apiculteur :
        # le recopier créerait des doublons, on ne le reprend pas.
        compte_napi: dict[str, int] = {}
        for h in hives:
            if not _blank(h.napi_number):
                k = _clean(h.napi_number).lower()
                compte_napi[k] = compte_napi.get(k, 0) + 1

        a_numeroter = [h for h in hives if _blank(h.number)]
        if not a_numeroter:
            return 0

        n = 1
        for h in a_numeroter:
            napi = _clean(h.napi_number) if not _blank(h.napi_number) else ""
            if napi and compte_napi.get(napi.lower(), 0) == 1 and napi.lower() not in pris:
                h.number = napi
                pris.add(napi.lower())
                try:
                    entiers.add(int(napi))
                except ValueError:
                    pass
                continue
            while n in entiers:
                n += 1
            h.number = str(n)
            entiers.add(n)
            pris.add(str(n))

        await db.commit()

    print(f"✅ {len(a_numeroter)} ruche(s) numérotée(s) automatiquement")
    return len(a_numeroter)


def hive_label(hive) -> str:
    """Libellé d'une ruche : le numéro d'abord, le nom en complément.

    Jamais la clé primaire : « Ruche #37 » exposait un identifiant technique
    que personne n'a choisi.
    """
    if hive is None:
        return "Ruche"
    numero = "" if _blank(getattr(hive, "number", None)) else _clean(hive.number)
    if not numero and not _blank(getattr(hive, "napi_number", None)):
        # Base pas encore renumérotée : mieux vaut l'ancien repère que rien.
        numero = _clean(hive.napi_number)
    nom = "" if _blank(getattr(hive, "name", None)) else _clean(hive.name)

    if numero and nom:
        return f"{numero} — {nom}"
    if numero:
        return f"Ruche {numero}"
    if nom:
        return nom
    return "Ruche sans numéro"
