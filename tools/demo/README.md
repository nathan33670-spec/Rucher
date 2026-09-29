# Démonstration publique

Ce dossier produit le jeu de données de la démonstration servie par GitHub
Pages (`.github/workflows/demo.yml`).

## Pourquoi un jeu écrit à la main

Pages ne sert que des fichiers statiques : il n'y a **pas de serveur** derrière
la démonstration, donc pas de base de données. L'API est simulée dans le
navigateur par `frontend/src/demo/adaptateur.js`, à partir de
`frontend/src/demo/donnees.json`.

Ce fichier est **généré**, jamais extrait d'une base réelle. Une extraction
embarquerait les débris des campagnes de test, et surtout ferait courir le
risque de publier des données réelles sur une page accessible à tous.

## Régénérer les données

```bash
python3 tools/demo/generer-donnees.py
```

Le tirage est reproductible : deux exécutions donnent le même résultat.

## Vérifier que les formes collent à l'API

Un jeu écrit à la main dérive vite — il suffit d'un champ mal nommé pour qu'un
écran reste vide, sans la moindre erreur. Le vérificateur compare les clés de
chaque réponse simulée à celles de l'API réelle :

```bash
# 1. pile de développement démarrée (docker compose up -d)
# 2. capturer une référence depuis l'API réelle, puis comparer
python3 tools/demo/verifier-formes.py
```

Il attend une capture dans `/tmp/reference-api.json`. C'est ainsi qu'ont été
trouvés `start_at` pris pour `starts_at`, et `counts` pour `yes_count` — deux
erreurs qui laissaient l'écran des événements désespérément vide.
