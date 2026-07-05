#!/usr/bin/env python3
"""🐝 Test Saison Apicole Complète — Rucher Manager
Simule: 10 membres, 3 ruchers, 15 ruches asso + 5 privées,
visites, récoltes, pots, ventes, trésorerie, inventaire.
"""
import requests, random, json
from datetime import datetime

BASE = "http://127.0.0.1:7080/api"
random.seed(42)

# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("🐝  TEST SAISON APICOLE COMPLÈTE")
print("=" * 60)

# ─── 0. Login admin ──────────────────────────────────────────
r = requests.post(f"{BASE}/users/login", json={"email": "admin@rucher.local", "password": "admin1234"})
assert r.status_code == 200, f"Login failed: {r.text}"
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print("✅ Connecté en admin\n")

# ─── 1. Création des 10 membres ──────────────────────────────
print("── 1. MEMBRES ──")
MEMBRES = [
    {"first_name": "Marie",   "last_name": "Dupont",   "email": "marie@rucher.local",   "roles": ["yard_manager"]},
    {"first_name": "Jean",    "last_name": "Martin",   "email": "jean@rucher.local",    "roles": ["yard_manager"]},
    {"first_name": "Sophie",  "last_name": "Bernard",  "email": "sophie@rucher.local",  "roles": ["treasurer"]},
    {"first_name": "Pierre",  "last_name": "Moreau",   "email": "pierre@rucher.local",  "roles": ["yard_manager"]},
    {"first_name": "Lucie",   "last_name": "Petit",    "email": "lucie@rucher.local",   "roles": ["user"]},
    {"first_name": "Antoine", "last_name": "Leroy",    "email": "antoine@rucher.local", "roles": ["user"]},
    {"first_name": "Claire",  "last_name": "Roux",     "email": "claire@rucher.local",  "roles": ["yard_manager"]},
    {"first_name": "Thomas",  "last_name": "Garcia",   "email": "thomas@rucher.local",  "roles": ["user"]},
    {"first_name": "Émilie",  "last_name": "Fournier", "email": "emilie@rucher.local",  "roles": ["user"]},
]

user_ids = [1]  # admin
for m in MEMBRES:
    r = requests.post(f"{BASE}/users/", json={
        "first_name": m["first_name"], "last_name": m["last_name"],
        "email": m["email"], "password": "test1234", "roles": m["roles"]
    }, headers=H)
    assert r.status_code == 201, f"Erreur création {m['first_name']} {m['last_name']}: {r.text}"
    user_ids.append(r.json()["id"])
    print(f"  👤 {m['first_name']} {m['last_name']} (id={r.json()['id']}, {m['roles']})")

yard_manager_ids = [user_ids[0], user_ids[1], user_ids[2], user_ids[4], user_ids[7]]
print(f"✅ {len(user_ids)} membres créés\n")

# ─── 2. Création des 3 ruchers ───────────────────────────────
print("── 2. RUCHERS ──")
RUCHERS = [
    {"name": "Les Tilleuls",   "location": "Chemin des Abeilles, 69001 Lyon",   "latitude": 45.764, "longitude": 4.835},
    {"name": "Les Acacias",    "location": "Route du Miel, 69003 Lyon",         "latitude": 45.753, "longitude": 4.858},
    {"name": "Le Châtaignier", "location": "Lieu-dit La Ruche, 69007 Lyon",     "latitude": 45.734, "longitude": 4.841},
]
apiary_ids = []
for a in RUCHERS:
    r = requests.post(f"{BASE}/apiaries/", json=a, headers=H)
    assert r.status_code == 201, f"Erreur rucher: {r.text}"
    apiary_ids.append(r.json()["id"])
    print(f"  🏕️ {a['name']} (id={r.json()['id']})")
print(f"✅ {len(apiary_ids)} ruchers\n")

# ─── 3. Création des 20 ruches (15 asso + 5 privées) ─────────
print("── 3. RUCHES ──")
hive_ids_asso = []
hive_ids_priv = []

for i in range(15):
    apiary_id = apiary_ids[i // 5]
    r = requests.post(f"{BASE}/apiaries/hives", json={
        "name": f"Asso-{i+1:02d}", "napi_number": f"FR-69-{1000+i}",
        "apiary_id": apiary_id,
        "ownership": "associative", "status": "active",
        "notes": f"Ruche associative #{i+1}",
        "manager_ids": [random.choice(yard_manager_ids)]
    }, headers=H)
    assert r.status_code == 201, f"Erreur ruche asso: {r.text}"
    hive_ids_asso.append(r.json()["id"])
    print(f"  🐝 Asso-{i+1:02d} → rucher {apiary_id} (asso)")

priv_owners = [user_ids[1], user_ids[2], user_ids[4], user_ids[5], user_ids[7]]
priv_apiaries = [apiary_ids[0], apiary_ids[0], apiary_ids[1], apiary_ids[1], apiary_ids[2]]
for i in range(5):
    r = requests.post(f"{BASE}/apiaries/hives", json={
        "name": f"Priv-{i+1:02d}", "napi_number": f"FR-69-{2000+i}",
        "apiary_id": priv_apiaries[i],
        "ownership": "private", "status": "active",
        "notes": f"Ruche privée #{i+1}",
        "manager_ids": [priv_owners[i]]
    }, headers=H)
    assert r.status_code == 201, f"Erreur ruche privée: {r.text}"
    hive_ids_priv.append(r.json()["id"])
    print(f"  🏠 Priv-{i+1:02d} → rucher {priv_apiaries[i]} (privée)")

all_hive_ids = hive_ids_asso + hive_ids_priv
print(f"✅ {len(hive_ids_asso)} asso + {len(hive_ids_priv)} privées = {len(all_hive_ids)} ruches\n")

# ─── 4. Visites (mars → septembre) ───────────────────────────
print("── 4. VISITES ──")
visit_count = 0
for month in range(3, 10):
    for fortnight in [1, 15]:
        visit_date = datetime(2026, month, fortnight, 10, 0).isoformat()
        hives_to_visit = random.sample(all_hive_ids, min(8, len(all_hive_ids)))
        for hive_id in hives_to_visit:
            if month <= 4:
                brood, reserves = random.randint(3, 6), random.randint(3, 5)
            elif month <= 7:
                brood, reserves = random.randint(6, 9), random.randint(5, 8)
            else:
                brood, reserves = random.randint(4, 7), random.randint(6, 9)
            supers_delta = random.choice([0, 0, 1, 1, 2]) if 5 <= month <= 7 else 0
            supers_count = random.randint(1, 3) if 5 <= month <= 7 else 0
            r = requests.post(f"{BASE}/visits/", json={
                "hive_id": hive_id, "visit_date": visit_date,
                "queen_seen": random.random() > 0.3,
                "brood_score": brood, "reserves_score": reserves,
                "supers_delta": supers_delta, "supers_count": supers_count,
                "notes": random.choice(["Colonie dynamique", "Reine vue, ponte régulière",
                    "Réserves correctes", "Belle activité au trou de vol"]),
            }, headers=H)
            if r.status_code == 201:
                visit_count += 1
print(f"✅ {visit_count} visites créées\n")

# ─── 5. Catégories de miel & Récoltes ────────────────────────
print("── 5. RÉCOLTES ──")
CATEGORIES = ["Acacia", "Toutes fleurs", "Châtaignier", "Lavande"]
cat_ids = []
for name in CATEGORIES:
    r = requests.post(f"{BASE}/honey/categories", json={"name": name}, headers=H)
    assert r.status_code == 201, f"Erreur catégorie: {r.text}"
    cat_ids.append(r.json()["id"])
    print(f"  🍯 Catégorie: {name}")

RECOLTES = [
    {"apiary_id": apiary_ids[0], "category_id": cat_ids[0], "ownership": "associative",
     "quantity_kg": 45.5, "nb_supers": 5, "nb_frames": 30,
     "harvest_date": "2026-06-10T09:00:00", "notes": "Acacia printemps, très bon cru"},
    {"apiary_id": apiary_ids[1], "category_id": cat_ids[1], "ownership": "associative",
     "quantity_kg": 38.0, "nb_supers": 4, "nb_frames": 24,
     "harvest_date": "2026-06-15T09:00:00", "notes": "Toutes fleurs, bon rendement"},
    {"apiary_id": apiary_ids[2], "category_id": cat_ids[2], "ownership": "associative",
     "quantity_kg": 52.0, "nb_supers": 6, "nb_frames": 36,
     "harvest_date": "2026-07-12T09:00:00", "notes": "Châtaignier corsé"},
    {"apiary_id": apiary_ids[0], "category_id": cat_ids[1], "ownership": "associative",
     "quantity_kg": 35.0, "nb_supers": 4, "nb_frames": 22,
     "harvest_date": "2026-07-25T09:00:00", "notes": "2ème récolte toutes fleurs"},
    {"apiary_id": apiary_ids[1], "category_id": cat_ids[3], "ownership": "associative",
     "quantity_kg": 28.5, "nb_supers": 3, "nb_frames": 18,
     "harvest_date": "2026-08-05T09:00:00", "notes": "Lavande, qualité top"},
    {"apiary_id": apiary_ids[0], "category_id": cat_ids[0], "ownership": "private",
     "quantity_kg": 12.0, "nb_supers": 2, "nb_frames": 8,
     "harvest_date": "2026-06-12T09:00:00", "notes": "Privée Marie — acacia"},
    {"apiary_id": apiary_ids[1], "category_id": cat_ids[1], "ownership": "private",
     "quantity_kg": 15.5, "nb_supers": 2, "nb_frames": 10,
     "harvest_date": "2026-07-14T09:00:00", "notes": "Privée Jean — toutes fleurs"},
    {"apiary_id": apiary_ids[2], "category_id": cat_ids[2], "ownership": "private",
     "quantity_kg": 8.0, "nb_supers": 1, "nb_frames": 6,
     "harvest_date": "2026-08-01T09:00:00", "notes": "Privée Pierre — châtaignier"},
]

harvest_ids = []
total_kg_asso, total_kg_priv = 0, 0
for rec in RECOLTES:
    r = requests.post(f"{BASE}/honey/", json=rec, headers=H)
    assert r.status_code == 201, f"Erreur récolte: {r.text}"
    harvest_ids.append(r.json()["id"])
    kg = rec["quantity_kg"]
    if rec["ownership"] == "associative": total_kg_asso += kg
    else: total_kg_priv += kg
    emoji = "🏛️" if rec["ownership"] == "associative" else "🏠"
    print(f"  {emoji} {kg}kg — {rec['notes']}")

print(f"✅ {len(harvest_ids)} récoltes | Asso: {total_kg_asso}kg, Privé: {total_kg_priv}kg\n")

# ─── 6. Mise en pot ──────────────────────────────────────────
print("── 6. POTS ──")
POTS = [
    {"harvest_id": harvest_ids[0], "ownership": "associative", "jar_weight_g": 500, "quantity": 60, "unit_price": 8.0},
    {"harvest_id": harvest_ids[0], "ownership": "associative", "jar_weight_g": 250, "quantity": 40, "unit_price": 5.0},
    {"harvest_id": harvest_ids[1], "ownership": "associative", "jar_weight_g": 500, "quantity": 50, "unit_price": 7.5},
    {"harvest_id": harvest_ids[2], "ownership": "associative", "jar_weight_g": 500, "quantity": 70, "unit_price": 9.0},
    {"harvest_id": harvest_ids[2], "ownership": "associative", "jar_weight_g": 250, "quantity": 30, "unit_price": 5.5},
    {"harvest_id": harvest_ids[3], "ownership": "associative", "jar_weight_g": 500, "quantity": 45, "unit_price": 7.5},
    {"harvest_id": harvest_ids[4], "ownership": "associative", "jar_weight_g": 500, "quantity": 35, "unit_price": 10.0},
    {"harvest_id": harvest_ids[4], "ownership": "associative", "jar_weight_g": 250, "quantity": 20, "unit_price": 6.0},
    {"harvest_id": harvest_ids[5], "ownership": "private", "jar_weight_g": 500, "quantity": 15, "unit_price": 8.0},
    {"harvest_id": harvest_ids[6], "ownership": "private", "jar_weight_g": 500, "quantity": 20, "unit_price": 7.5},
    {"harvest_id": harvest_ids[7], "ownership": "private", "jar_weight_g": 250, "quantity": 20, "unit_price": 5.0},
]

jar_ids = []
for pot in POTS:
    r = requests.post(f"{BASE}/honey/jars", json=pot, headers=H)
    assert r.status_code == 201, f"Erreur pot: {r.text}"
    jar_ids.append(r.json()["id"])
    emoji = "🏛️" if pot["ownership"] == "associative" else "🏠"
    print(f"  🫙 {emoji} {pot['quantity']}x {pot['jar_weight_g']}g @ {pot['unit_price']}€")

print(f"✅ {len(jar_ids)} lots de pots\n")

# ─── 7. Ventes ────────────────────────────────────────────────
print("── 7. VENTES ──")
VENTES = [
    {"jar_id": jar_ids[0], "quantity": 10, "buyer": "Marché de Vaise"},
    {"jar_id": jar_ids[0], "quantity": 5,  "buyer": "Mme Leblanc"},
    {"jar_id": jar_ids[1], "quantity": 8,  "buyer": "Fête du miel"},
    {"jar_id": jar_ids[2], "quantity": 12, "buyer": "Épicerie Bio du Coin"},
    {"jar_id": jar_ids[3], "quantity": 15, "buyer": "Marché Croix-Rousse"},
    {"jar_id": jar_ids[6], "quantity": 6,  "buyer": "M. Durand — lavande"},
    {"jar_id": jar_ids[8], "quantity": 5,  "buyer": "Vente privée Marie"},
    {"jar_id": jar_ids[9], "quantity": 8,  "buyer": "Amis de Jean"},
]

total_ventes = 0
for v in VENTES:
    r = requests.post(f"{BASE}/honey/sales", json=v, headers=H)
    assert r.status_code == 201, f"Erreur vente: {r.text}"
    sale = r.json()
    total_ventes += sale["total_amount"]
    print(f"  💰 {v['quantity']}x → {sale['total_amount']:.2f}€ — {v['buyer']}")

print(f"✅ {len(VENTES)} ventes = {total_ventes:.2f}€\n")

# ─── 8. Trésorerie ───────────────────────────────────────────
print("── 8. TRÉSORERIE ──")
TRANSACTIONS = [
    *[{"transaction_type": "income", "category": "membership", "amount": 30.0,
       "description": f"Cotisation 2026 — {MEMBRES[i-1]['first_name'] + ' ' + MEMBRES[i-1]['last_name'] if i > 0 else 'Admin'}",
       "date": f"2026-01-{10+i:02d}T10:00:00"} for i in range(10)],
    {"transaction_type": "expense", "category": "material", "amount": 250.0,
     "description": "10 cadres de corps Dadant", "supplier": "Apidistri", "date": "2026-03-05T10:00:00"},
    {"transaction_type": "expense", "category": "material", "amount": 180.0,
     "description": "5 hausses Dadant complètes", "supplier": "Thomas Apiculture", "date": "2026-04-10T10:00:00"},
    {"transaction_type": "expense", "category": "material", "amount": 95.0,
     "description": "Enfumoir + lève-cadre", "supplier": "Apidistri", "date": "2026-03-15T10:00:00"},
    {"transaction_type": "expense", "category": "material", "amount": 320.0,
     "description": "Extracteur 4 cadres tangentiel", "supplier": "Lega France", "date": "2026-05-20T10:00:00"},
    {"transaction_type": "expense", "category": "treatment", "amount": 85.0,
     "description": "Apivar — 20 lanières varroa", "supplier": "Véto-Pharma", "date": "2026-08-15T10:00:00"},
    {"transaction_type": "expense", "category": "treatment", "amount": 45.0,
     "description": "Acide oxalique 3.5%", "supplier": "Véto-Pharma", "date": "2026-09-10T10:00:00"},
]

total_in, total_out = 0, 0
for tx in TRANSACTIONS:
    r = requests.post(f"{BASE}/treasury/", json=tx, headers=H)
    assert r.status_code == 201, f"Erreur transaction: {r.text}"
    if tx["transaction_type"] == "income": total_in += tx["amount"]
    else: total_out += tx["amount"]

print(f"  📈 Cotisations: {total_in:.2f}€")
print(f"  📉 Dépenses: {total_out:.2f}€")
print(f"✅ {len(TRANSACTIONS)} transactions\n")

# ─── 9. Inventaire ───────────────────────────────────────────
print("── 9. INVENTAIRE ──")
INVENTAIRE = [
    {"name": "Corps Dadant 10c", "category": "Ruche", "location": "Local asso", "quantity": 8, "unit": "unité", "alert_threshold": 3},
    {"name": "Hausse Dadant", "category": "Ruche", "location": "Local asso", "quantity": 12, "unit": "unité", "alert_threshold": 5},
    {"name": "Cadre de corps ciré", "category": "Cadre", "location": "Local asso", "quantity": 50, "unit": "unité", "alert_threshold": 20},
    {"name": "Cadre de hausse ciré", "category": "Cadre", "location": "Local asso", "quantity": 40, "unit": "unité", "alert_threshold": 15},
    {"name": "Enfumoir inox", "category": "Outil", "location": "Local asso", "quantity": 3, "unit": "unité"},
    {"name": "Combinaison apiculteur", "category": "Protection", "location": "Local asso", "quantity": 6, "unit": "unité"},
    {"name": "Gants cuir", "category": "Protection", "location": "Local asso", "quantity": 10, "unit": "paire"},
    {"name": "Lève-cadre", "category": "Outil", "location": "Local asso", "quantity": 4, "unit": "unité"},
    {"name": "Extracteur tangentiel 4c", "category": "Extraction", "location": "Miellerie", "quantity": 1, "unit": "unité"},
    {"name": "Bac à désoperculer", "category": "Extraction", "location": "Miellerie", "quantity": 2, "unit": "unité"},
    {"name": "Maturateur 50kg", "category": "Extraction", "location": "Miellerie", "quantity": 2, "unit": "unité"},
    {"name": "Pot 500g verre", "category": "Conditionnement", "location": "Miellerie", "quantity": 200, "unit": "unité", "alert_threshold": 50},
    {"name": "Pot 250g verre", "category": "Conditionnement", "location": "Miellerie", "quantity": 150, "unit": "unité", "alert_threshold": 30},
    {"name": "Lanière Apivar", "category": "Traitement", "location": "Local asso", "quantity": 20, "unit": "unité"},
    {"name": "Acide oxalique 3.5%", "category": "Traitement", "location": "Local asso", "quantity": 5, "unit": "flacon"},
]

for item in INVENTAIRE:
    r = requests.post(f"{BASE}/inventory/", json=item, headers=H)
    assert r.status_code == 201, f"Erreur inventaire: {r.text}"
    print(f"  📦 {item['name']}: {item['quantity']} {item['unit']}")

print(f"✅ {len(INVENTAIRE)} articles\n")

# ─── 10. Stats miel ──────────────────────────────────────────
print("── 10. STATS MIEL ──")
stats = requests.get(f"{BASE}/honey/stats", headers=H).json()
print(f"  Production totale: {stats['total_kg']} kg ({stats['nb_harvests']} récoltes)")
for own in stats.get("by_ownership", []):
    emoji = "🏛️" if own["ownership"] == "associative" else "🏠"
    print(f"  {emoji} {own['ownership']}: {own['total_kg']} kg")
for cat in stats.get("by_category", []):
    print(f"  🍯 {cat['category']}: {cat['total_kg']} kg")

stock = requests.get(f"{BASE}/honey/jars/stock", headers=H).json()
print("\n  📦 Stock de pots:")
for s in stock:
    emoji = "🏛️" if s["ownership"] == "associative" else "🏠"
    print(f"    {emoji} {s['jar_weight_g']}g: {s['stock']} restants (vendus: {s['sold']})")

# ─── 11. Bilan final ─────────────────────────────────────────
r_treasury = requests.get(f"{BASE}/treasury/", headers=H).json()
income = sum(t["amount"] for t in r_treasury if t["transaction_type"] == "income")
expense = sum(t["amount"] for t in r_treasury if t["transaction_type"] == "expense")

print()
print("=" * 60)
print("🏆  BILAN SAISON APICOLE 2026")
print("=" * 60)
print(f"  👥 Membres:           {len(user_ids)}")
print(f"  🏕️ Ruchers:           {len(apiary_ids)}")
print(f"  🐝 Ruches:            {len(all_hive_ids)} (15 asso + 5 privées)")
print(f"  📋 Visites:           {visit_count}")
print(f"  🍯 Production:        {stats['total_kg']} kg")
print(f"     • Associatif:     {total_kg_asso} kg")
print(f"     • Privé:          {total_kg_priv} kg")
print(f"     • Moy/ruche asso: {total_kg_asso/15:.1f} kg")
print(f"  🫙 Pots créés:        {sum(p['quantity'] for p in POTS)}")
print(f"  💰 Ventes:            {len(VENTES)} ({total_ventes:.2f}€)")
print(f"  📈 Trésorerie:")
print(f"     Recettes:         {income:.2f}€")
print(f"     Dépenses:         {expense:.2f}€")
print(f"     Solde:            {income - expense:+.2f}€")
print(f"  📦 Inventaire:        {len(INVENTAIRE)} articles")
print("=" * 60)
print("✅ TOUS LES TESTS ONT RÉUSSI !")
print("=" * 60)
