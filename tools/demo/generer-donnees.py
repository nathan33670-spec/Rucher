#!/usr/bin/env python3
"""Génère le jeu de données de la démonstration publique.

La démo tourne sans backend : l'application est servie en fichiers statiques
et un adaptateur remplace l'API par ces réponses. Ce jeu est donc **écrit
ici**, et non extrait d'une base — une extraction embarquerait les débris des
campagnes de test, et surtout ferait courir le risque de publier des données
réelles sur une page accessible à tous.

Tout ce qui suit est inventé : personnes, ruchers, montants. Les formes des
réponses, elles, sont celles de l'API réelle.

    python3 tools/demo/generer-donnees.py
"""

import json
import os
import random
from datetime import datetime, timedelta

random.seed(2026)  # jeu reproductible : deux exécutions donnent le même résultat

AUJOURDHUI = datetime(2026, 9, 28, 18, 0, 0)


def iso(d):
    return d.isoformat()


# ─────────────────────────── Adhérents ───────────────────────────
PERSONNES = [
    ("Marie", "Santini", ["admin"]),
    ("Paul", "Leroy", ["treasurer"]),
    ("Antoine", "Casanova", ["yard_manager"]),
    ("Claire", "Bonnet", ["yard_manager"]),
    ("Jean", "Ferrandi", ["user"]),
    ("Sophie", "Mariani", ["user"]),
    ("Luc", "Pieri", ["user"]),
    ("Hélène", "Rossi", ["user"]),
    ("Thomas", "Grimaldi", ["user"]),
    ("Nadine", "Valentini", ["user"]),
    ("Pierre", "Colombani", ["user"]),
    ("Julie", "Agostini", ["readonly"]),
]

utilisateurs = []
for i, (prenom, nom, roles) in enumerate(PERSONNES, start=1):
    utilisateurs.append({
        "id": i,
        "email": f"{prenom.lower()}.{nom.lower()}",
        "contact_email": f"{prenom.lower()}.{nom.lower()}@exemple.fr",
        "phone": None,
        "first_name": prenom,
        "last_name": nom,
        "is_active": True,
        "roles": roles,
        "selectable_roles": roles + (["user", "readonly"] if roles != ["readonly"] else []),
        "active_role": roles[0],
        "default_role": roles[0],
        "created_at": iso(AUJOURDHUI - timedelta(days=400 - i * 7)),
    })

MOI = dict(utilisateurs[0])  # la démo se connecte en administratrice

# ─────────────────────────── Ruchers ───────────────────────────
RUCHERS = [
    (1, "Rucher du Maquis", "Route de Cauro, 20117 Eccica-Suarella", 41.9012, 8.9341,
     "Exposition sud-est, à l'abri du libeccio. Miellée d'arbousier en automne."),
    (2, "Rucher de la Gravona", "Plaine de la Gravona, 20128 Tavaco", 42.0154, 8.9622,
     "En bord de rivière, floraison précoce. Accès en 4×4 après les pluies."),
    (3, "Rucher École", "Jardin partagé, 20000 Ajaccio", 41.9270, 8.7369,
     "Rucher pédagogique de l'association : c'est ici que se font les formations."),
]

ruchers = []
for rid, nom, adresse, lat, lon, desc in RUCHERS:
    ruchers.append({
        "id": rid, "name": nom, "address": adresse,
        "latitude": lat, "longitude": lon, "description": desc,
        "created_at": iso(AUJOURDHUI - timedelta(days=500)),
        "hives_count": 0, "photo_url": None,
    })

# ─────────────────────────── Ruches ───────────────────────────
NOMS_RUCHES = [
    "La Doyenne", "L'Arbousière", "La Bourdonnante", "Le Maquis", "La Vaillante",
    "L'Essaim de mai", "La Tranquille", "La Bleue", "La Généreuse", "Le Chêne-liège",
    "La Petite", "L'Immortelle", "La Châtaigneraie", "La Sauvage", "La Colline",
    "Le Ruisseau", "La Bergerie", "La Ferme",
]

REPARTITION = [(1, 7), (2, 6), (3, 5)]   # rucher -> nombre de ruches
PRIVEES = {4, 9, 13}                     # quelques ruches appartiennent à un adhérent

ruches = []
numero = 1
for rid, combien in REPARTITION:
    for _ in range(combien):
        privee = numero in PRIVEES
        proprietaire = utilisateurs[(numero % 8) + 3] if privee else None
        ruches.append({
            "id": numero,
            "apiary_id": rid,
            "number": str(numero),
            "napi_number": f"NAPI-{4400 + numero}",
            "name": NOMS_RUCHES[numero - 1],
            "ownership": "private" if privee else "associative",
            "position_x": round(random.uniform(0.15, 0.85), 3),
            "position_y": round(random.uniform(0.15, 0.85), 3),
            "status": "active",
            "notes": "",
            "managers": ([{"id": proprietaire["id"],
                           "first_name": proprietaire["first_name"],
                           "last_name": proprietaire["last_name"]}] if proprietaire else []),
            "apiary_name": next(r["name"] for r in ruchers if r["id"] == rid),
            "photo_url": None,
            "created_at": iso(AUJOURDHUI - timedelta(days=480 - numero)),
        })
        numero += 1

for r in ruchers:
    r["hives_count"] = sum(1 for h in ruches if h["apiary_id"] == r["id"])

# ─────────────────────────── Visites ───────────────────────────
COMMENTAIRES = [
    "Colonie très populeuse, pensé à poser une hausse supplémentaire.",
    "Reine vue, ponte régulière sur cinq cadres.",
    "Réserves un peu justes, nourrissement au sirop.",
    "Quelques cellules royales en bordure, à surveiller.",
    "Rien à signaler, colonie calme.",
    "Traces de varroa sur le lange, comptage à prévoir.",
    "Hausse pleine, récolte à programmer la semaine prochaine.",
    "Cadres de rive à remplacer au printemps.",
    "",
]

visites = []
vid = 1
auteurs = [u["id"] for u in utilisateurs[:5]]
for h in ruches:
    # Entre 6 et 10 visites étalées sur la saison, la plus récente en premier.
    for k in range(random.randint(6, 10)):
        jour = AUJOURDHUI - timedelta(days=k * random.randint(9, 16) + random.randint(0, 4))
        if jour < AUJOURDHUI - timedelta(days=200):
            break
        alerte = random.random() < 0.05
        visites.append({
            "id": vid,
            "hive_id": h["id"],
            "author_id": random.choice(auteurs),
            "visited_at": iso(jour.replace(hour=random.randint(9, 17), minute=random.choice([0, 15, 30, 45]))),
            "created_at": iso(jour.replace(hour=random.randint(9, 18))),
            "queen_seen": random.choice([True, True, True, False, None]),
            "brood_score": random.randint(3, 9),
            "reserves_score": random.randint(2, 9),
            "supers_count": random.randint(0, 3),
            "frames_count": random.choice([8, 9, 10, 10, 10]),
            "supers_delta": 0,
            "feeding": random.choice([None, None, None, "Sirop 50/50", "Candi"]),
            "comment": random.choice(COMMENTAIRES) or None,
            "is_alert": alerte,
            "alert_message": "Colonie faible, à revoir rapidement." if alerte else None,
            "honey_harvest_kg": None,
            "pollen_harvest_kg": None,
            "treatment_type": None,
            "treatment_product": None,
            "synced": True,
            "hive_name": h["name"],
            "hive_number": h["number"],
            "author_name": "",   # renseigné juste après, une fois la table des noms prête
            "is_live_mode": False,
        })
        vid += 1

par_id = {u["id"]: f"{u['first_name']} {u['last_name']}" for u in utilisateurs}
for v in visites:
    v["author_name"] = par_id[v["author_id"]]

visites.sort(key=lambda v: v["visited_at"], reverse=True)

# « /visits/last » ne renvoie qu'un résumé, pas la visite complète : reprendre
# l'objet entier ferait diverger la démonstration de l'application réelle.
CHAMPS_RESUME = ("id", "visited_at", "queen_seen", "brood_score", "reserves_score",
                 "supers_count", "frames_count", "feeding", "is_alert", "author_name")
dernieres = {}
for v in visites:
    cle = str(v["hive_id"])
    if cle not in dernieres:
        dernieres[cle] = {c: v[c] for c in CHAMPS_RESUME}

# ─────────────────────────── Miellée ───────────────────────────
CATEGORIES_MIEL = [
    {"id": 1, "name": "Maquis de printemps", "color": "#C9A227",
     "description": "Bruyère, ciste et lavande, récolté fin mai."},
    {"id": 2, "name": "Châtaignier", "color": "#8B5E3C",
     "description": "Corsé et peu sucré, typique de la Castagniccia."},
    {"id": 3, "name": "Arbousier", "color": "#A33B20",
     "description": "Amer et rare, la dernière miellée de l'année."},
    {"id": 4, "name": "Miellat", "color": "#4F4032", "description": None},
]

recoltes = []
hid = 1
for mois, cat in ((5, 1), (6, 1), (7, 2), (9, 3)):
    for _ in range(random.randint(3, 6)):
        ruche = random.choice(ruches)
        recoltes.append({
            "id": hid,
            "apiary_id": ruche["apiary_id"],
            "hive_id": ruche["id"],
            "category_id": cat,
            "ownership": ruche["ownership"],
            "harvest_date": iso(datetime(2026, mois, random.randint(3, 27), 11, 0)),
            "quantity_kg": float(random.randint(8, 26)),
            "loss_kg": 0.0,
            "nb_frames": random.randint(6, 10),
            "nb_supers": random.randint(1, 3),
            "notes": None,
            "created_by": 1,
            "created_at": iso(datetime(2026, mois, random.randint(3, 27), 18, 0)),
            "category_name": next(c["name"] for c in CATEGORIES_MIEL if c["id"] == cat),
            "apiary_name": ruche["apiary_name"],
            "hive_name": ruche["name"],
            "jars": [],
        })
        hid += 1

total_miel = sum(r["quantity_kg"] for r in recoltes)
par_categorie = {}
for r in recoltes:
    e = par_categorie.setdefault(r["category_name"], {"category": r["category_name"],
                                                     "total_kg": 0.0, "nb_harvests": 0})
    e["total_kg"] += r["quantity_kg"]
    e["nb_harvests"] += 1
par_mois = {}
for r in recoltes:
    m = int(r["harvest_date"][5:7])
    par_mois[m] = par_mois.get(m, 0.0) + r["quantity_kg"]

POTS = [
    {"id": 1, "category_id": 1, "category_name": "Maquis de printemps", "size_g": 250,
     "quantity": 48, "unit_price": 7.5},
    {"id": 2, "category_id": 1, "category_name": "Maquis de printemps", "size_g": 500,
     "quantity": 31, "unit_price": 13.0},
    {"id": 3, "category_id": 2, "category_name": "Châtaignier", "size_g": 500,
     "quantity": 22, "unit_price": 14.0},
    {"id": 4, "category_id": 3, "category_name": "Arbousier", "size_g": 250,
     "quantity": 16, "unit_price": 9.0},
]

VENTES = [
    {"id": 1, "date": iso(AUJOURDHUI - timedelta(days=12)), "buyer": "Marché de Mezzavia",
     "total": 168.0, "nb_jars": 14, "notes": None},
    {"id": 2, "date": iso(AUJOURDHUI - timedelta(days=31)), "buyer": "Épicerie du cours",
     "total": 260.0, "nb_jars": 20, "notes": None},
    {"id": 3, "date": iso(AUJOURDHUI - timedelta(days=54)), "buyer": "Fête du miel",
     "total": 412.5, "nb_jars": 39, "notes": "Stand de l'association"},
]

# ─────────────────────────── Sanitaire ───────────────────────────
sanitaires = []
sid = 1
for ruche in ruches[:10]:
    sanitaires.append({
        "id": sid, "hive_id": ruche["id"], "hive_name": ruche["name"],
        "record_type": "treatment",
        "treatment_type": "varroa",
        "application_date": "2026-08-12", "end_date": "2026-09-23",
        "product": "Apivar", "dosage": "2 lanières", "varroa_count": None,
        "notes": "Traitement d'été, pose simultanée sur tout le rucher.",
        "performed_by": 3, "created_at": iso(datetime(2026, 8, 12, 19, 0)),
    })
    sid += 1
for ruche in ruches[:6]:
    sanitaires.append({
        "id": sid, "hive_id": ruche["id"], "hive_name": ruche["name"],
        "record_type": "count",
        "treatment_type": None,
        "application_date": "2026-09-05", "end_date": None,
        "product": None, "dosage": None, "varroa_count": random.randint(0, 12),
        "notes": "Comptage sur lange, 72 h.",
        "performed_by": 3, "created_at": iso(datetime(2026, 9, 5, 18, 0)),
    })
    sid += 1

# ─────────────────────────── Inventaire ───────────────────────────
MATERIEL = [
    ("Hausses Dadant", "Ruches et hausses", "Local Ajaccio", 34, "unité", 5, 22.0),
    ("Corps Dadant 10 cadres", "Ruches et hausses", "Local Ajaccio", 12, "unité", 3, 48.0),
    ("Cadres filés", "Cadres", "Local Ajaccio", 180, "unité", 40, 1.8),
    ("Cire gaufrée", "Cadres", "Local Ajaccio", 14, "kg", 5, 18.5),
    ("Lanières Apivar", "Sanitaire", "Armoire sanitaire", 40, "unité", 10, 2.6),
    ("Acide oxalique", "Sanitaire", "Armoire sanitaire", 3, "kg", 1, 24.0),
    ("Enfumoirs", "Outillage", "Local Ajaccio", 6, "unité", 2, 32.0),
    ("Lève-cadres", "Outillage", "Local Ajaccio", 9, "unité", 3, 9.5),
    ("Vareuses", "Protection", "Local Ajaccio", 11, "unité", 4, 45.0),
    ("Gants", "Protection", "Local Ajaccio", 2, "paire", 6, 12.0),
    ("Pots 250 g", "Conditionnement", "Miellerie", 220, "unité", 60, 0.55),
    ("Pots 500 g", "Conditionnement", "Miellerie", 95, "unité", 60, 0.75),
    ("Étiquettes", "Conditionnement", "Miellerie", 400, "unité", 100, 0.09),
    ("Maturateur 100 kg", "Miellerie", "Miellerie", 2, "unité", 1, 210.0),
    ("Extracteur 9 cadres", "Miellerie", "Miellerie", 1, "unité", 1, 890.0),
]

inventaire = []
for i, (nom, cat, lieu, qte, unite, seuil, prix) in enumerate(MATERIEL, start=1):
    inventaire.append({
        "id": i, "name": nom, "category": cat, "location": lieu,
        "quantity": qte, "unit": unite, "alert_threshold": seuil,
        "unit_price": prix, "qr_code": None,
        "owner_user_id": None, "owner_name": None,
        "created_at": iso(AUJOURDHUI - timedelta(days=300 - i)),
    })

alertes = [x for x in inventaire if x["alert_threshold"] and x["quantity"] <= x["alert_threshold"]]

lieux = {}
for x in inventaire:
    e = lieux.setdefault(x["location"], {"location": x["location"], "item_count": 0,
                                         "total_qty": 0, "total_value": 0.0})
    e["item_count"] += 1
    e["total_qty"] += x["quantity"]
    e["total_value"] += x["quantity"] * (x["unit_price"] or 0)
for e in lieux.values():
    e["total_value"] = round(e["total_value"], 2)

# ─────────────────────────── Trésorerie ───────────────────────────
ECRITURES = [
    ("income", "membership", 840.0, "Cotisations 2026 (28 adhérents)", None, 3, 14),
    ("income", "sales", 412.5, "Fête du miel — stand", None, 8, 5),
    ("income", "sales", 260.0, "Épicerie du cours", None, 8, 28),
    ("income", "sales", 168.0, "Marché de Mezzavia", None, 9, 16),
    ("income", "subsidy", 500.0, "Subvention communale", "Mairie d'Ajaccio", 4, 9),
    ("expense", "equipment", 264.0, "12 hausses Dadant", "Apiculture Corse", 3, 22),
    ("expense", "equipment", 210.0, "Maturateur 100 kg", "Apiculture Corse", 6, 11),
    ("expense", "health", 104.0, "Lanières Apivar (40)", "Coopérative apicole", 7, 30),
    ("expense", "packaging", 189.5, "Pots et étiquettes", "Verrerie du Sud", 8, 19),
    ("expense", "insurance", 156.0, "Assurance responsabilité civile", "Assureur", 1, 15),
    ("expense", "other", 78.4, "Carburant déplacements ruchers", None, 9, 12),
    ("expense", "food", 92.0, "Repas assemblée générale", None, 2, 24),
]

tresorerie = []
for i, (sens, cat, montant, libelle, fournisseur, mois, jour) in enumerate(ECRITURES, start=1):
    d = datetime(2026, mois, jour, 0, 0)
    tresorerie.append({
        "id": i,
        "transaction_type": sens,
        "category": cat,
        "amount": montant,
        "description": libelle,
        "supplier": fournisseur,
        "date": iso(d),
        "source": "manual",
        "reconciled_at": iso(d + timedelta(days=6)) if mois <= 8 else None,
        "created_by": 2,
        "invoices": [],
        "created_at": iso(d + timedelta(days=1)),
    })

recettes = sum(t["amount"] for t in tresorerie if t["transaction_type"] == "income")
depenses = sum(t["amount"] for t in tresorerie if t["transaction_type"] == "expense")

rapprochements = []
for m in range(9, 0, -1):
    lignes = [t for t in tresorerie if int(t["date"][5:7]) == m]
    pointees = [t for t in lignes if t["reconciled_at"]]
    rapprochements.append({
        "year": 2026, "month": m,
        "label": f"{['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre'][m]} 2026",
        "validated": m <= 8 and bool(lignes),
        "validated_at": iso(datetime(2026, m, 28, 20, 0)) if (m <= 8 and lignes) else None,
        "total": len(lignes), "reconciled": len(pointees),
        "pending": len(lignes) - len(pointees),
    })

# ─────────────────────────── Événements ───────────────────────────
evenements = [
    {"id": 1, "title": "Assemblée générale",
     "description": "Bilan de la saison, comptes de l'exercice et renouvellement du "
                    "bureau. Un pot suivra, chacun apporte quelque chose.",
     "location": "Salle des fêtes, Ajaccio",
     "start_at": iso(datetime(2026, 10, 12, 14, 0)),
     "end_at": iso(datetime(2026, 10, 12, 17, 0)),
     "is_public": True, "created_by": 1,
     "created_at": iso(AUJOURDHUI - timedelta(days=9)),
     "my_response": "yes", "counts": {"yes": 18, "maybe": 4, "no": 2},
     "last_notified_at": iso(AUJOURDHUI - timedelta(days=9))},
    {"id": 2, "title": "Traitement anti-varroa — Rucher du Maquis",
     "description": "Pose des lanières sur l'ensemble du rucher. Prévoir vareuse "
                    "et enfumoir.",
     "location": "Rucher du Maquis, Eccica-Suarella",
     "start_at": iso(datetime(2026, 10, 4, 9, 30)),
     "end_at": iso(datetime(2026, 10, 4, 12, 0)),
     "is_public": True, "created_by": 3,
     "created_at": iso(AUJOURDHUI - timedelta(days=4)),
     "my_response": None, "counts": {"yes": 7, "maybe": 2, "no": 0},
     "last_notified_at": None},
    {"id": 3, "title": "Formation débutants : préparer l'hivernage",
     "description": "Séance au rucher école. Ouverte aux adhérents de première année.",
     "location": "Rucher École, Ajaccio",
     "start_at": iso(datetime(2026, 10, 18, 10, 0)),
     "end_at": iso(datetime(2026, 10, 18, 12, 30)),
     "is_public": True, "created_by": 4,
     "created_at": iso(AUJOURDHUI - timedelta(days=2)),
     "my_response": "maybe", "counts": {"yes": 11, "maybe": 5, "no": 1},
     "last_notified_at": None},
    {"id": 4, "title": "Récolte d'arbousier",
     "description": "Récolte de la dernière miellée de l'année, puis extraction "
                    "à la miellerie.",
     "location": "Rucher de la Gravona, Tavaco",
     "start_at": iso(datetime(2026, 9, 6, 8, 30)),
     "end_at": iso(datetime(2026, 9, 6, 13, 0)),
     "is_public": True, "created_by": 1,
     "created_at": iso(AUJOURDHUI - timedelta(days=30)),
     "my_response": "yes", "counts": {"yes": 9, "maybe": 1, "no": 3},
     "last_notified_at": iso(AUJOURDHUI - timedelta(days=30))},
]

# ─────────────────────────── Campagnes de courriel ───────────────────────────
campagnes = [
    {"id": 1, "subject": "Assemblée générale du 12 octobre", "audience": "all",
     "audience_label": "Tous les adhérents", "tracking": True,
     "sent_at": iso(AUJOURDHUI - timedelta(days=9)),
     "sent_count": 28, "failed_count": 0, "opened_count": 21, "clicked_count": 12,
     "attachments_count": 1, "author_name": "Marie Santini"},
    {"id": 2, "subject": "Rappel : traitement anti-varroa avant le 30 septembre",
     "audience": "all", "audience_label": "Tous les adhérents", "tracking": True,
     "sent_at": iso(AUJOURDHUI - timedelta(days=24)),
     "sent_count": 28, "failed_count": 1, "opened_count": 15, "clicked_count": 6,
     "attachments_count": 0, "author_name": "Antoine Casanova"},
    {"id": 3, "subject": "Point de trésorerie du bureau", "audience": "admin",
     "audience_label": "Administrateurs", "tracking": False,
     "sent_at": iso(AUJOURDHUI - timedelta(days=40)),
     "sent_count": 3, "failed_count": 0, "opened_count": 0, "clicked_count": 0,
     "attachments_count": 2, "author_name": "Paul Leroy"},
]

# ─────────────────────────── Journal et cloche ───────────────────────────
journal = []
for i, (qui, quoi, entite, quand) in enumerate([
    (1, "create", "event", 2), (3, "create", "sanitary", 23), (2, "create", "transaction", 16),
    (1, "mail_campaign", "mail", 9), (4, "create", "visit", 1), (3, "update", "hive", 5),
    (2, "reconciliation_validated", "treasury", 31), (1, "create", "user", 48),
], start=1):
    journal.append({
        "id": 100 - i, "user_id": qui, "user_name": par_id[qui],
        "action": quoi, "entity_type": entite, "entity_id": i,
        "details": None,
        "created_at": iso(AUJOURDHUI - timedelta(days=quand, hours=i)),
    })

boite = [
    {"id": 1, "category": "events", "title": "📅 Assemblée générale",
     "body": "Le 12 octobre à 14 h, salle des fêtes d'Ajaccio.",
     "url": "/app/events", "created_at": iso(AUJOURDHUI - timedelta(days=9)), "read": False},
    {"id": 2, "category": "visits", "title": "🐝 Nouvelle visite",
     "body": "Antoine a saisi une visite — 3 — La Bourdonnante",
     "url": "/app/visits", "created_at": iso(AUJOURDHUI - timedelta(days=1)), "read": False},
    {"id": 3, "category": "sanitary", "title": "💊 Traitement enregistré",
     "body": "Apivar posé sur 10 ruches du Rucher du Maquis.",
     "url": "/app/sanitary", "created_at": iso(AUJOURDHUI - timedelta(days=47)), "read": True},
]

# ─────────────────────────── Notes de version ───────────────────────────
# Lues dans le produit lui-même : les recopier ici les ferait vieillir dès la
# prochaine version, et la démonstration annoncerait des nouveautés périmées.
_versions = {}
_fichier = os.path.join(os.path.dirname(__file__), "..", "..",
                        "backend", "app", "releases.py")
with open(os.path.normpath(_fichier), encoding="utf-8") as f:
    exec(compile(f.read(), "releases.py", "exec"), _versions)
RELEASES = _versions.get("RELEASES", [])


# ─────────────────────────── Assemblage ───────────────────────────
mois_courant = sum(1 for v in visites
                   if v["visited_at"][:7] == AUJOURDHUI.strftime("%Y-%m"))

donnees = {
    "/users/me": MOI,
    "/users/": utilisateurs,
    "/apiaries/": ruchers,
    "/apiaries/hives/all": ruches,
    "_hives_by_apiary": {str(r["id"]): [h for h in ruches if h["apiary_id"] == r["id"]]
                         for r in ruchers},
    "/visits/": visites,
    "/visits/stats": {"month": mois_courant, "total": len(visites)},
    "/visits/last": dernieres,
    "/inventory/": inventaire,
    "/inventory/alerts": alertes,
    "/inventory/locations/summary": sorted(lieux.values(), key=lambda e: e["location"]),
    "/honey/": sorted(recoltes, key=lambda r: r["harvest_date"], reverse=True),
    "/honey/categories": CATEGORIES_MIEL,
    "/honey/jars": POTS,
    "/honey/jars/stock": POTS,
    "/honey/sales": VENTES,
    "/honey/private-users": [],
    "/honey/stats": {
        "year": 2026, "total_kg": total_miel, "nb_harvests": len(recoltes),
        "by_category": sorted(par_categorie.values(), key=lambda e: -e["total_kg"]),
        "by_month": [{"month": m, "total_kg": v} for m, v in sorted(par_mois.items())],
        "by_ownership": [{"ownership": "associative", "total_kg": total_miel,
                          "nb_harvests": len(recoltes)}],
    },
    "/sanitary/": sanitaires,
    "/treasury/": sorted(tresorerie, key=lambda t: t["date"], reverse=True),
    "/treasury/summary": {"year": 2026, "income": round(recettes, 2),
                          "expense": round(depenses, 2),
                          "balance": round(recettes - depenses, 2)},
    "/treasury/invoices/": [],
    "/treasury/reconciliation": rapprochements,
    "/events/": evenements,
    "/visit-plans/": [],
    "/docs/": [],
    "/releases/": {"current": RELEASES[0]["version"] if RELEASES else None,
                   "releases": RELEASES},
    "/audit/": journal,
    "/notifications/inbox": {"unread": sum(1 for m in boite if not m["read"]),
                             "messages": boite},
    "/notifications/preferences": {
        "enabled": True, "visits": True, "visits_mine": True, "visits_assoc": True,
        "visits_private_others": True, "inventory": True, "alerts": True,
        "sanitary": True, "treasury": True, "events": True,
    },
    "/notifications/preferences/capabilities": {"treasury": True,
                                                "visits_private_others": True},
    "/settings/access": {"treasury_read_all": False, "audit_read_all": False},
    "/settings/weather/association": {
        "ideal": {"hour_start": 10, "hour_end": 18, "temp_min": 15.0, "temp_max": 30.0,
                  "rain_max": 30.0, "wind_max": 25.0, "min_hours": 2},
        "ok": {"temp_min": 12.0, "rain_max": 50.0, "wind_max": 35.0},
    },
    "/settings/weather/mine": {
        "personal": False,
        "criteria": {
            "ideal": {"hour_start": 10, "hour_end": 18, "temp_min": 15, "temp_max": 30,
                      "rain_max": 30, "wind_max": 25, "min_hours": 2},
            "ok": {"temp_min": 12, "rain_max": 50, "wind_max": 35},
        },
    },
    "/mail/audiences": [
        {"key": "all", "label": "Tous les adhérents", "count": 12},
        {"key": "admin", "label": "Administrateurs", "count": 1},
        {"key": "yard_manager", "label": "Responsables de rucher", "count": 2},
        {"key": "treasurer", "label": "Trésoriers", "count": 1},
        {"key": "user", "label": "Usagers", "count": 7},
    ],
    "/mail/campaigns": campagnes,
}

sortie = os.path.join(os.path.dirname(__file__), "..", "..",
                      "frontend", "src", "demo", "donnees.json")
sortie = os.path.normpath(sortie)
os.makedirs(os.path.dirname(sortie), exist_ok=True)
with open(sortie, "w", encoding="utf-8") as f:
    json.dump(donnees, f, ensure_ascii=False, separators=(",", ":"))

print(f"{len(utilisateurs)} adhérents, {len(ruchers)} ruchers, {len(ruches)} ruches, "
      f"{len(visites)} visites, {len(recoltes)} récoltes, {len(tresorerie)} écritures")
print(f"Écrit dans {sortie} — {os.path.getsize(sortie) // 1024} Ko")
