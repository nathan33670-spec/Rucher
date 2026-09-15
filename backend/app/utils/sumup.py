"""Liaison avec SumUp : encaissements par l'API, relevé par fichier.

Ce que l'API SumUp permet, et ce qu'elle ne permet pas — la distinction
commande toute l'organisation de ce module :

- ``/v2.1/merchants/{code}/transactions/history`` liste les **paiements
  entrants** (encaissements, remboursements, impayés) ;
- ``/v1.0/merchants/{code}/payouts`` liste les **virements et les retenues** :
  on y trouve les **commissions** prélevées par SumUp (champ ``fee``), les
  retours de prélèvement et les ajustements de solde. Ce sont de vraies
  sorties d'argent, et elles sont bien accessibles par l'API ;
- en revanche, les **achats réglés avec la carte du compte professionnel**
  n'ont aucune API : ni relevé, ni compte pro, ni facture SumUp Invoice dans
  la spécification. Ils n'arrivent que par l'export CSV du relevé, d'où le
  second lecteur de ce module.

Le partage entre les deux sources évite le double compte : un remboursement
figure à la fois dans l'historique des transactions et comme retenue sur un
virement. Il n'est retenu qu'une fois, côté transactions.

Chaque écriture importée garde la référence SumUp dont elle provient : c'est
ce qui rend les deux voies rejouables sans jamais créer de doublon.
"""

import csv
import io
import os
import re
from datetime import datetime, timedelta

import httpx

# Redirigeable pour les essais : la liaison ne serait pas éprouvable
# autrement, faute de pouvoir créer un vrai compte marchand.
API_BASE = os.getenv("SUMUP_API_BASE", "https://api.sumup.com").rstrip("/")

# Bornes de sécurité : sans elles, une première synchronisation remonterait
# toute l'histoire du compte et saturerait la trésorerie.
DEFAULT_LOOKBACK_DAYS = 90
MAX_PAGES = 20
PAGE_SIZE = 100


def config_defaults() -> dict:
    return {
        "api_key": "",
        "merchant_code": "",
        "lookback_days": DEFAULT_LOOKBACK_DAYS,
        "enabled": False,
    }


class SumUpError(Exception):
    """Erreur exploitable telle quelle par l'interface."""


def _headers(cfg: dict) -> dict:
    cle = (cfg.get("api_key") or "").strip()
    if not cle:
        raise SumUpError(
            "Aucune clé d'API SumUp enregistrée : renseignez-la dans "
            "Réglages → Configuration."
        )
    return {"Authorization": f"Bearer {cle}", "Accept": "application/json"}


async def fetch_merchant_code(cfg: dict) -> str:
    """Code marchand associé à la clé, quand il n'a pas été saisi."""
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{API_BASE}/v0.1/me", headers=_headers(cfg))
    if r.status_code == 401:
        raise SumUpError("Clé d'API SumUp refusée : vérifiez-la dans votre tableau de bord SumUp.")
    if r.status_code >= 400:
        raise SumUpError(f"SumUp a répondu {r.status_code} à la lecture du profil marchand.")
    data = r.json() or {}
    code = (data.get("merchant_profile") or {}).get("merchant_code") or ""
    if not code:
        raise SumUpError("SumUp n'a pas renvoyé de code marchand pour cette clé.")
    return code


async def fetch_transactions(cfg: dict, since: datetime) -> list[dict]:
    """Encaissements SumUp depuis une date, normalisés.

    La pagination se fait par lien « next » renvoyé par SumUp ; on la borne
    pour qu'une configuration inattendue ne fasse pas tourner la requête
    indéfiniment.
    """
    code = (cfg.get("merchant_code") or "").strip()
    if not code:
        code = await fetch_merchant_code(cfg)

    url = f"{API_BASE}/v2.1/merchants/{code}/transactions/history"
    params = {
        "oldest_time": since.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "limit": PAGE_SIZE,
        "order": "ascending",
    }
    sorties: list[dict] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(MAX_PAGES):
            r = await client.get(url, headers=_headers(cfg), params=params)
            if r.status_code == 401:
                raise SumUpError(
                    "Clé d'API SumUp refusée : vérifiez-la dans votre tableau de bord SumUp."
                )
            if r.status_code == 403:
                raise SumUpError(
                    "La clé d'API SumUp n'a pas le droit de lire l'historique "
                    "des transactions (portée « transactions.history »)."
                )
            if r.status_code >= 400:
                raise SumUpError(f"SumUp a répondu {r.status_code} : {r.text[:200]}")
            data = r.json() or {}
            for item in data.get("items", []):
                normalisee = _normalise_transaction(item)
                if normalisee:
                    sorties.append(normalisee)
            suivant = _next_link(data)
            if not suivant:
                break
            url, params = suivant, None
    return sorties


def _next_link(data: dict) -> str | None:
    for lien in data.get("links") or []:
        if (lien.get("rel") or "").lower() == "next" and lien.get("href"):
            href = lien["href"]
            return href if href.startswith("http") else API_BASE + href
    return None


def _normalise_transaction(item: dict) -> dict | None:
    """Transaction SumUp → écriture de trésorerie, ou None si à ignorer."""
    statut = (item.get("status") or "").upper()
    # Un paiement échoué ou annulé n'a jamais touché le compte : l'inscrire
    # fausserait le bilan.
    if statut not in ("SUCCESSFUL", "REFUNDED"):
        return None

    montant = item.get("amount")
    if montant is None:
        return None
    montant = float(montant)

    type_ = (item.get("type") or "PAYMENT").upper()
    # Un remboursement sort de la caisse : c'est une dépense.
    sortant = type_ in ("REFUND", "CHARGE_BACK")

    ref = item.get("transaction_code") or item.get("id")
    if not ref:
        return None

    horodatage = _parse_date(item.get("timestamp"))
    libelle = item.get("product_summary") or ""
    if type_ == "REFUND":
        libelle = f"Remboursement {libelle}".strip()
    elif type_ == "CHARGE_BACK":
        libelle = f"Impayé {libelle}".strip()

    return {
        "external_ref": f"sumup:{ref}",
        "amount": abs(montant),
        "is_expense": sortant,
        "date": horodatage or datetime.utcnow(),
        "description": (libelle or "Encaissement SumUp")[:500],
        "supplier": item.get("card_type") or None,
        "source": "sumup-api",
    }


def _parse_date(valeur) -> datetime | None:
    if not valeur:
        return None
    texte = str(valeur).strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(texte)
    except ValueError:
        for motif in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
                      "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y"):
            try:
                d = datetime.strptime(texte, motif)
                break
            except ValueError:
                continue
        else:
            return None
    # Les colonnes de la base sont naïves : une date portant un fuseau y
    # déclencherait une erreur à l'insertion.
    return d.replace(tzinfo=None) if d.tzinfo else d


# ── Relevé du compte professionnel (CSV) ──────────────────────────────
#
# SumUp n'expose pas le compte professionnel : le relevé ne s'obtient qu'en
# téléchargeant un fichier. Ses en-têtes changent selon la langue et le pays,
# d'où ces familles de noms acceptés plutôt qu'une liste figée.

COLONNES_DATE = ("date", "date de la transaction", "transaction date", "date de valeur",
                 "value date", "date d'opération", "date operation", "created at",
                 "date et heure", "timestamp")
COLONNES_MONTANT = ("montant", "amount", "montant (eur)", "amount (eur)", "value",
                    "somme", "montant total", "total")
COLONNES_DEBIT = ("débit", "debit", "sortie", "retrait")
COLONNES_CREDIT = ("crédit", "credit", "entrée", "entree", "dépôt", "depot")
COLONNES_LIBELLE = ("description", "libellé", "libelle", "intitulé", "intitule",
                    "détails", "details", "objet", "référence", "reference",
                    "bénéficiaire", "beneficiaire", "contrepartie", "counterparty",
                    "type de transaction", "transaction type", "nom")
COLONNES_REF = ("id", "identifiant", "transaction id", "id de transaction",
                "référence de transaction", "transaction reference", "code")


def _trouve(entetes: list[str], candidats: tuple) -> str | None:
    for c in candidats:
        if c in entetes:
            return c
    # Repli : une colonne qui contient le mot-clé (« Date de l'opération »).
    for e in entetes:
        for c in candidats:
            if c in e:
                return e
    return None


def _montant(valeur) -> float | None:
    """Nombre d'un tableur français ou anglais, signe conservé."""
    if valeur is None:
        return None
    texte = str(valeur).strip()
    if not texte:
        return None
    negatif = texte.startswith("-") or (texte.startswith("(") and texte.endswith(")"))
    # Retirer devises, espaces insécables et séparateurs de milliers.
    texte = re.sub(r"[^\d,.\-]", "", texte)
    texte = texte.lstrip("-")
    if "," in texte and "." in texte:
        # Le dernier séparateur rencontré est le décimal.
        if texte.rfind(",") > texte.rfind("."):
            texte = texte.replace(".", "").replace(",", ".")
        else:
            texte = texte.replace(",", "")
    elif "," in texte:
        texte = texte.replace(",", ".")
    if not texte:
        return None
    try:
        v = float(texte)
    except ValueError:
        return None
    return -v if negatif else v


def parse_statement_csv(contenu: bytes) -> list[dict]:
    """Relevé SumUp (CSV) → écritures normalisées.

    Lève ``SumUpError`` avec les en-têtes réellement lus quand le fichier ne
    ressemble pas à un relevé : mieux vaut dire ce qu'on a vu que renvoyer un
    « format invalide » sur lequel personne ne peut agir.
    """
    texte = contenu.decode("utf-8-sig", errors="replace")
    premiere = texte.splitlines()[0] if texte.strip() else ""
    if not premiere:
        raise SumUpError("Le fichier est vide.")

    separateur = max(";,\t", key=premiere.count)
    if premiere.count(separateur) == 0:
        separateur = ","

    lecteur = csv.DictReader(io.StringIO(texte), delimiter=separateur)
    entetes = [(f or "").strip().lower() for f in (lecteur.fieldnames or [])]
    lecteur.fieldnames = entetes

    col_date = _trouve(entetes, COLONNES_DATE)
    col_montant = _trouve(entetes, COLONNES_MONTANT)
    col_debit = _trouve(entetes, COLONNES_DEBIT)
    col_credit = _trouve(entetes, COLONNES_CREDIT)
    col_libelle = _trouve(entetes, COLONNES_LIBELLE)
    col_ref = _trouve(entetes, COLONNES_REF)

    if not col_date or not (col_montant or col_debit or col_credit):
        raise SumUpError(
            "Ce fichier ne ressemble pas à un relevé SumUp : il faut une "
            "colonne de date et une colonne de montant. Colonnes trouvées : "
            + (", ".join(entetes) or "aucune")
        )

    lignes = []
    for i, brute in enumerate(lecteur, start=2):
        quand = _parse_date(brute.get(col_date))
        if not quand:
            continue

        if col_montant:
            valeur = _montant(brute.get(col_montant))
        else:
            valeur = None
        if valeur is None and col_credit:
            credit = _montant(brute.get(col_credit))
            if credit:
                valeur = abs(credit)
        if valeur is None and col_debit:
            debit = _montant(brute.get(col_debit))
            if debit:
                valeur = -abs(debit)
        if valeur is None or valeur == 0:
            continue

        libelle = (brute.get(col_libelle) or "").strip() if col_libelle else ""
        ref = (brute.get(col_ref) or "").strip() if col_ref else ""
        if not ref:
            # Sans identifiant dans le fichier, on en fabrique un stable à
            # partir de la ligne : c'est lui qui évite les doublons au
            # réimport du même relevé.
            ref = "|".join([quand.strftime("%Y-%m-%d"), f"{valeur:.2f}", libelle[:60]])

        lignes.append({
            "external_ref": f"sumup-csv:{ref}"[:250],
            "amount": abs(valeur),
            "is_expense": valeur < 0,
            "date": quand,
            "description": (libelle or "Opération SumUp")[:500],
            "supplier": None,
            "source": "sumup-csv",
            "ligne": i,
        })
    return lignes


# ── Virements et retenues ─────────────────────────────────────────────
#
# Ce que chaque enregistrement devient, et pourquoi :
#
# - ``fee``                   → dépense. C'est la commission SumUp, elle
#                               n'apparaît nulle part ailleurs ;
# - ``BALANCE_DEDUCTION``     → dépense. Ajustement de solde, sans contrepartie
#                               dans l'historique des transactions ;
# - ``DD_RETURN_DEDUCTION``   → dépense. Un retour de prélèvement n'est pas une
#                               transaction carte, il n'est donc pas déjà compté ;
# - ``PAYOUT``                → ignoré. C'est le virement du solde vers la
#                               banque : l'encaissement a déjà été compté, le
#                               réinscrire doublerait les recettes ;
# - ``REFUND_DEDUCTION`` et
#   ``CHARGE_BACK_DEDUCTION`` → ignorés. Ce sont les retenues correspondant aux
#                               remboursements et impayés déjà repris de
#                               l'historique des transactions.

RETENUES_A_COMPTER = ("BALANCE_DEDUCTION", "DD_RETURN_DEDUCTION")
RETENUES_DEJA_COMPTEES = ("REFUND_DEDUCTION", "CHARGE_BACK_DEDUCTION")

LIBELLES_RETENUE = {
    "BALANCE_DEDUCTION": "Ajustement de solde SumUp",
    "DD_RETURN_DEDUCTION": "Retour de prélèvement SumUp",
}


async def fetch_payouts(cfg: dict, debut: datetime, fin: datetime) -> list[dict]:
    """Commissions et retenues SumUp, normalisées comme des dépenses.

    ``start_date`` et ``end_date`` sont obligatoires côté SumUp, d'où les deux
    bornes plutôt qu'une simple ancienneté.
    """
    code = (cfg.get("merchant_code") or "").strip()
    if not code:
        code = await fetch_merchant_code(cfg)

    url = f"{API_BASE}/v1.0/merchants/{code}/payouts"
    params = {
        "start_date": debut.strftime("%Y-%m-%d"),
        "end_date": fin.strftime("%Y-%m-%d"),
        "format": "json",
        "limit": PAGE_SIZE,
        "order": "asc",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=_headers(cfg), params=params)
    if r.status_code == 401:
        raise SumUpError("Clé d'API SumUp refusée : vérifiez-la dans votre tableau de bord SumUp.")
    if r.status_code == 403:
        raise SumUpError(
            "La clé d'API SumUp n'a pas le droit de lire les virements "
            "(portée « payouts.read »)."
        )
    if r.status_code >= 400:
        raise SumUpError(f"SumUp a répondu {r.status_code} : {r.text[:200]}")

    data = r.json() or []
    # SumUp renvoie une liste ; certains environnements l'enveloppent.
    if isinstance(data, dict):
        data = data.get("items") or data.get("payouts") or []

    lignes = []
    for item in data:
        lignes.extend(_normalise_payout(item))
    return lignes


def _normalise_payout(item: dict) -> list[dict]:
    """Un enregistrement de virement → zéro, une ou deux dépenses."""
    if (item.get("status") or "SUCCESSFUL").upper() == "FAILED":
        return []

    identifiant = item.get("id")
    if identifiant is None:
        return []
    type_ = (item.get("type") or "PAYOUT").upper()
    quand = _parse_date(item.get("date")) or datetime.utcnow()
    sorties = []

    # La commission accompagne aussi bien un virement qu'une retenue.
    frais = item.get("fee")
    try:
        frais = float(frais) if frais is not None else 0.0
    except (TypeError, ValueError):
        frais = 0.0
    if frais > 0:
        sorties.append({
            "external_ref": f"sumup-fee:{identifiant}",
            "amount": round(frais, 2),
            "is_expense": True,
            "date": quand,
            "description": "Commission SumUp",
            "supplier": "SumUp",
            "source": "sumup-api",
        })

    if type_ in RETENUES_A_COMPTER:
        montant = item.get("amount")
        try:
            montant = abs(float(montant)) if montant is not None else 0.0
        except (TypeError, ValueError):
            montant = 0.0
        if montant > 0:
            libelle = LIBELLES_RETENUE.get(type_, "Retenue SumUp")
            ref_op = item.get("transaction_code") or item.get("reference")
            if ref_op:
                libelle = f"{libelle} ({ref_op})"
            sorties.append({
                "external_ref": f"sumup-payout:{identifiant}",
                "amount": round(montant, 2),
                "is_expense": True,
                "date": quand,
                "description": libelle[:500],
                "supplier": "SumUp",
                "source": "sumup-api",
            })
    return sorties
