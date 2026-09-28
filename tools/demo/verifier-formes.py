"""Compare les formes du jeu de démonstration à celles de l'API réelle.

Un jeu écrit à la main dérive vite : il suffit d'un champ mal nommé pour
qu'un écran reste vide sans la moindre erreur. On compare donc les clés, et
on refuse les différences plutôt que de les découvrir à l'usage.
"""
import json
import sys

demo = json.load(open("/home/user/Rucher/frontend/src/demo/donnees.json"))
ref = json.load(open("/tmp/reference-api.json"))

# Équivalences de chemins entre la capture et le jeu de démonstration.
ALIAS = {
    "/visits/": "/visits/?limit=100",
    "/treasury/reconciliation": "/treasury/reconciliation?months=12",
    "/audit/": "/audit/?limit=50",
}

# Dictionnaires indexés par identifiant : comparer les clés n'aurait aucun
# sens, ce sont des numéros de ruche. On compare la forme des valeurs.
INDEXES_PAR_ID = {"/visits/last"}

IGNORER = {"_hives_by_apiary", "_seq"}

def cles(x):
    if isinstance(x, list):
        return cles(x[0]) if x else None
    if isinstance(x, dict):
        return set(x.keys())
    return None

problemes = []
verifies = 0
for chemin, valeur in demo.items():
    if chemin in IGNORER:
        continue
    source = ALIAS.get(chemin, chemin)
    attendu = ref.get(source)
    if attendu is None:
        for variante in (source + "/", source.rstrip("/")):
            if variante in ref:
                attendu = ref[variante]
                break
    if attendu is None:
        print(f"  ?  {chemin} — pas de référence, non vérifié")
        continue

    if chemin in INDEXES_PAR_ID:
        attendu = next(iter(attendu.values()), None) if isinstance(attendu, dict) else None
        valeur = next(iter(valeur.values()), None) if isinstance(valeur, dict) else None
        if attendu is None or valeur is None:
            continue

    a, b = cles(attendu), cles(valeur)
    if a is None or b is None:
        continue
    verifies += 1
    manquantes = a - b
    inconnues = b - a
    if manquantes or inconnues:
        problemes.append((chemin, sorted(manquantes), sorted(inconnues)))

print(f"\n{verifies} formes comparées")
if problemes:
    print(f"\n{len(problemes)} écart(s) :\n")
    for chemin, manquantes, inconnues in problemes:
        print(f"  {chemin}")
        if manquantes:
            print(f"      absent du jeu de démo : {', '.join(manquantes)}")
        if inconnues:
            print(f"      inventé (inexistant côté API) : {', '.join(inconnues)}")
    sys.exit(1)
print("Toutes les formes correspondent à l'API réelle.")
