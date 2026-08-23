# Matrice des droits — Rucher Manager

> Document généré à partir du code (`backend/app/routers/*.py`, `backend/app/utils/auth.py`).
> Les droits sont **appliqués côté serveur** : masquer un bouton dans l'interface
> ne protège rien, c'est la dépendance `require_roles(...)` de chaque route qui fait foi.

## 1. Les cinq rôles

| Rôle | Code | Destiné à |
|---|---|---|
| Administrateur | `admin` | Bureau de l'association — accès total |
| Trésorier | `treasurer` | Comptabilité, factures, ventes |
| Responsable de rucher | `yard_manager` | Conduite technique des ruchers et du cheptel |
| Usager | `user` | Adhérent qui suit ses propres ruches |
| Lecture seule | `readonly` | Consultation (⚠️ voir §5 — non appliqué) |

**Cumul** : un compte peut porter plusieurs rôles. `admin` court-circuite tous les
contrôles (`require_roles` renvoie immédiatement si `admin` est présent).

**Rôle actif** : un utilisateur multi-rôles peut restreindre ses droits à un seul
rôle, à la volée ou par défaut. Le rôle actif est porté par le jeton JWT et
`get_user_roles()` ne renvoie alors que celui-ci — la restriction est donc
**réellement appliquée côté serveur**, pas seulement affichée.

---

## 2. Matrice par module

Légende : ✅ autorisé · ⛔ refusé (403) · 🔶 conditionnel (voir notes)

### Ruchers et ruches

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Voir les ruchers / ruches | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer / modifier un rucher | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Supprimer un rucher | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Photo de rucher (ajout / suppression) | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Créer une ruche | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Modifier une ruche | ✅ | ⛔ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Photo de ruche | ✅ | ⛔ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Supprimer une ruche | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |

¹ Uniquement si l'utilisateur est **gestionnaire déclaré** de cette ruche.

### Visites

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter les visites | ✅ | ✅ | ✅ | ✅ | ✅ |
| Saisir une visite | ✅ | 🔶 ¹ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Modifier une visite | ✅ | 🔶 ¹ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Supprimer une visite | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Planifier ses visites (météo) | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ `_check_hive_access` : admin et yard_manager passent partout ; les autres
doivent être **gestionnaires de la ruche** concernée.

### Suivi sanitaire

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter le registre | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enregistrer un **traitement** | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Enregistrer un **comptage varroa** | ✅ | 🔶 ¹ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Modifier une entrée | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Supprimer une entrée | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |

¹ Uniquement sur ses propres ruches (gestionnaire déclaré).

> Un traitement saisi pendant une visite alimente automatiquement ce registre.
> Il suit les droits de la **visite**, pas ceux du registre sanitaire.

### Inventaire

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter le stock et les alertes | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer / modifier un article | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Entrée / sortie de stock | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Déplacer un article | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Supprimer un article | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Définir la **propriété** d'un article | ✅ | ✅ | ✅ | ⛔ | ⛔ |

> La « propriété » est une donnée descriptive (association ou utilisateur).
> Elle **ne confère aucun droit** : elle n'empêche pas un gestionnaire de
> modifier un article appartenant à quelqu'un d'autre.

### Miellée

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter les récoltes | ✅ | 🔶 ¹ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Créer une récolte **privée** | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer une récolte **associative** | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Supprimer une récolte privée | 🔶 ² | 🔶 ² | 🔶 ² | 🔶 ² | 🔶 ² |
| Supprimer une récolte associative | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Vendre un pot **privé** | 🔶 ² | 🔶 ² | 🔶 ² | 🔶 ² | 🔶 ² |
| Vendre un pot **associatif** | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Gérer les catégories de miel | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |

¹ admin / yard_manager voient tout ; les autres voient l'associatif + leur privé.
² Le créateur, ou un responsable (admin / yard_manager).

### Trésorerie

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter les écritures et le bilan | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer / modifier / supprimer une écriture | ✅ | ✅ | ⛔ | ⛔ | ⛔ |
| Joindre une facture | ✅ | ✅ | ⛔ | ⛔ | ⛔ |
| Télécharger une facture | ✅ | ✅ | ✅ | ✅ | ✅ |

> ⚠️ La **lecture** de la trésorerie est ouverte à tout compte connecté, y
> compris le téléchargement des factures. L'onglet est masqué dans le menu pour
> les non-trésoriers, mais l'API reste accessible. Voir §5.

### Événements

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Voir les événements | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer / modifier / supprimer | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Répondre (présent / absent) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Voir la liste des participants | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |

### Utilisateurs et réglages

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Lister les comptes | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Créer / modifier / supprimer un compte | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Attribuer les rôles | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Réinitialiser le mot de passe d'un tiers | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Changer **son propre** mot de passe | ✅ | ✅ | ✅ | ✅ | ✅ |
| Changer **son** rôle actif / par défaut | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ |
| Import CSV de comptes | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Lire les critères météo | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Régler** les critères météo | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Documentation : écrire / supprimer | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Notifications : s'abonner, régler ses préférences | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ Uniquement parmi les rôles **déjà attribués** par un administrateur.
Toute autre valeur est refusée (403), y compris en forgeant la requête.

### Journal d'activité

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter le journal complet | ✅ | ✅ | ✅ | ✅ | ✅ |

> ⚠️ Ouvert à tout compte connecté. Voir §5.

---

## 3. Accès sans authentification

| Ressource | Accès |
|---|---|
| Site vitrine (`/`, chapitres, quiz) | Public |
| Documentation publiée (`GET /api/docs/`) | Public |
| Toute autre route `/api/**` | Jeton requis (401 sinon) |

---

## 4. Durée de session

| Cas | Durée du jeton |
|---|---|
| Connexion simple | 30 jours |
| « Rester connecté sur cet appareil » | 10 ans |

Les jetons sont **auto-portés** : révoquer un accès suppose de désactiver le
compte (`is_active = false`), ce qui invalide le jeton au prochain appel.
Changer le mot de passe n'invalide **pas** les jetons déjà émis.

---

## 5. Écarts connus (à arbitrer)

Ces points sont des **choix actuels du code**, pas des bugs de mise en œuvre.
Ils sont listés pour décision.

| # | Constat | Portée | Correctif possible |
|---|---|---|---|
| 1 | Le rôle `readonly` **n'est contrôlé nulle part**. Un compte `readonly` a exactement les droits d'un `user` : il peut saisir des visites sur ses ruches, créer des récoltes privées, compter les varroas. | Moyenne | Ajouter un refus explicite en écriture pour ce rôle |
| 2 | La **trésorerie est lisible par tous** les comptes connectés (écritures, bilan, téléchargement des factures). Le menu est masqué, l'API ne l'est pas. | Moyenne | Restreindre `GET /api/treasury/**` à admin + trésorier |
| 3 | Le **journal d'activité est lisible par tous**. Il expose qui a fait quoi sur l'ensemble de l'association. | Faible à moyenne | Restreindre `GET /api/audit/` aux administrateurs |
| 4 | Un jeton « rester connecté » vit **10 ans** et survit à un changement de mot de passe. | Moyenne | Ajouter un identifiant de session invalidable, ou réduire la durée |
| 5 | La **propriété d'un article d'inventaire ne protège pas** l'article : tout gestionnaire peut le modifier. | Faible (voulu) | Documenter, ou restreindre si souhaité |

> Aucun de ces points n'expose les données **hors** de l'association : toutes ces
> routes exigent un compte valide. Il s'agit de cloisonnement **entre adhérents**.
