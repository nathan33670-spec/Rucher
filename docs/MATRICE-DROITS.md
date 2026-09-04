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
| Lecture seule | `readonly` | Consultation stricte — aucune écriture possible |

**Cumul** : un compte peut porter plusieurs rôles. `admin` court-circuite tous les
contrôles (`require_roles` renvoie immédiatement si `admin` est présent).

**Rôle actif** : un utilisateur peut restreindre ses droits à un seul rôle, à la
volée (puce en haut à droite) ou par défaut (menu profil). Le rôle actif est
porté par le jeton JWT et `get_user_roles()` ne renvoie alors que celui-ci — la
restriction est donc **réellement appliquée côté serveur**, pas seulement
affichée.

**Hiérarchie des rôles** : on peut toujours *descendre* en droits, jamais monter.
Chaque rôle « contient » les rôles moins étendus, qui deviennent donc
sélectionnables sans avoir été attribués :

| Rôle attribué | Rôles sélectionnables |
|---|---|
| `admin` | admin, treasurer, yard_manager, user, readonly |
| `treasurer` | treasurer, user, readonly |
| `yard_manager` | yard_manager, user, readonly |
| `user` | user, readonly |
| `readonly` | readonly |

Un administrateur peut ainsi travailler « en usager » au quotidien pour éviter
les fausses manœuvres, et reprendre ses droits en deux clics. L'inverse est
impossible : demander un rôle hors de cette liste renvoie 403, même en forgeant
la requête. La liste est calculée par `get_selectable_roles()` et exposée dans
`GET /api/users/me` (champ `selectable_roles`).

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

### Cloisonnement du miel privé — vérifié

Le privé est isolé **par personne**, pas seulement « privé vs associatif » :

- Marion ne voit ni les récoltes, ni les pots, ni les statistiques de Thomas,
  et réciproquement. Chacun voit l'associatif **plus** son propre privé.
- Le total affiché sur le tableau de bord est filtré de la même façon : il
  n'additionne jamais le privé d'autrui.
- Un membre ne peut pas vendre ni modifier un pot qui ne lui appartient pas.
- Le paramètre `user_id` est **ignoré** pour un non-responsable : impossible de
  s'en servir pour consulter les données d'un autre adhérent.
- La liste des propriétaires de miel privé (`/honey/private-users`) est
  refusée (403) aux non-responsables.

Les administrateurs et responsables de rucher voient l'ensemble, et disposent
dans l'onglet **Privé** d'un sélecteur « Voir les données privées de… » pour
n'afficher qu'une personne à la fois.

### Trésorerie

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter les écritures et le bilan | ✅ | ✅ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ |
| Créer / modifier / supprimer une écriture | ✅ | ✅ | ⛔ | ⛔ | ⛔ |
| Joindre une facture | ✅ | ✅ | ⛔ | ⛔ | ⛔ |
| Télécharger une facture | ✅ | ✅ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ |

¹ Refusé par défaut. Un administrateur peut ouvrir la trésorerie **en lecture
seule** à tous les membres depuis *Réglages → Configuration → Cloisonnement des
accès*. La saisie reste réservée aux administrateurs et trésoriers.

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

¹ Uniquement parmi ses rôles **sélectionnables** (rôles attribués + rôles moins
étendus qu'ils impliquent, cf. § 1). Toute autre valeur est refusée (403), y
compris en forgeant la requête.

### Journal d'activité

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter le journal complet | ✅ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ |

¹ Refusé par défaut ; ouvrable à tous depuis *Réglages → Configuration*.

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

**Révocation.** Chaque compte porte un compteur `token_version` inscrit dans le
jeton. Il est incrémenté à chaque changement de mot de passe — par l'utilisateur
comme par un administrateur — ce qui **périme immédiatement tous les jetons
émis auparavant**, sur tous les appareils.

- L'appareil depuis lequel l'utilisateur change son mot de passe reçoit un
  jeton neuf : il reste connecté.
- Une réinitialisation par un administrateur déconnecte le compte **partout**.
- Désactiver un compte (`is_active = false`) invalide aussi l'accès au
  prochain appel.
- Les jetons émis avant cette fonctionnalité restent valables jusqu'au
  prochain changement de mot de passe (pas de déconnexion générale au
  déploiement).

---

## 5. Écarts connus (à arbitrer)

Ces points sont des **choix actuels du code**, pas des bugs de mise en œuvre.
Ils sont listés pour décision.

| # | Constat | Portée | Statut |
|---|---|---|---|
| 1 | Le rôle `readonly` n'était contrôlé nulle part. | Moyenne | ✅ **Corrigé** — toute écriture est refusée (403), voir §6 |
| 2 | La trésorerie était lisible par tous les comptes connectés. | Moyenne | ✅ **Corrigé** — réservée au bureau, ouverture en lecture optionnelle |
| 3 | Le journal d'activité était lisible par tous. | Faible à moyenne | ✅ **Corrigé** — réservé aux administrateurs, ouverture optionnelle |
| 4 | Un jeton survivait à un changement de mot de passe. | Moyenne | ✅ **Corrigé** — voir §4 |
| 5 | La propriété d'un article d'inventaire ne protège pas l'article : tout gestionnaire peut le modifier. | Faible (voulu) | Choix assumé — champ descriptif, pas un droit |

> Aucun de ces points n'exposait les données **hors** de l'association : toutes
> ces routes exigent un compte valide. Il s'agissait de cloisonnement **entre
> adhérents**.

---

## 6. Le rôle « lecture seule » en détail

Un compte dont les droits **effectifs** se limitent à `readonly` se voit refuser
toute requête d'écriture (`POST`, `PUT`, `PATCH`, `DELETE`) sur l'ensemble de
l'API, avec le message :

> *Votre compte est en lecture seule : modification impossible.*

Le contrôle est fait à un point unique (`get_current_user`), il couvre donc
**toutes** les routes, y compris celles ajoutées plus tard.

**Exceptions — strictement personnelles :**

| Route | Pourquoi |
|---|---|
| `PUT /api/users/me/password` | Doit pouvoir changer son propre mot de passe |
| `POST /api/users/switch-role` | Changer de rôle actif |
| `PUT /api/users/me/default-role` | Choisir son rôle par défaut |
| `POST /api/notifications/subscribe` / `unsubscribe` | Gérer les notifications de son appareil |
| `PUT /api/notifications/preferences` | Régler ses propres notifications |
| `POST /api/notifications/test` | Tester ses notifications |

**Conséquence à connaître :** un compte en lecture seule **ne peut pas répondre
à un événement** (présent / absent), ni planifier une visite. Si cela s'avère
trop restrictif, dites-le : ces deux routes peuvent être ajoutées aux
exceptions.

**Cumul de rôles.** Un compte portant `readonly` **et** un autre rôle conserve
les droits de l'autre rôle. La restriction ne s'applique que si l'utilisateur
sélectionne explicitement « Lecture seule » comme rôle actif — ce qui en fait
un mode « consultation » utilisable volontairement.
