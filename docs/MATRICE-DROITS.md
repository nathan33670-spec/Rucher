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
| Modifier une ruche (dont son n° de ruche) | ✅ | ⛔ | ✅ | 🔶 ¹ | 🔶 ¹ |
| **Déplacer** une ruche vers un autre rucher | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Photo de ruche | ✅ | ⛔ | ✅ | 🔶 ¹ | 🔶 ¹ |
| Supprimer une ruche | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |

¹ Uniquement si l'utilisateur est **gestionnaire déclaré** de cette ruche.
En lecture seule, l'écriture reste refusée quoi qu'il arrive.

> **Le numéro affiché n'est jamais l'identifiant de base.** Une ruche sans
> numéro s'affichait auparavant « Ruche #37 » : un numéro que personne n'a
> choisi et que l'on ne peut pas modifier. Toute ruche créée sans numéro en
> reçoit désormais un (le premier entier libre), modifiable ensuite ; au
> démarrage, les ruches existantes qui n'avaient ni numéro ni NAPI sont
> numérotées de la même façon.
>
> **Deux numéros à ne pas confondre :**
>
> - le **numéro de ruche** identifie *une* ruche (souvent peint dessus). Il doit
>   rester unique dans toute l'application, ruchers confondus — une ruche garde
>   son numéro en changeant de rucher, un contrôle limité à un rucher créerait
>   donc des doublons au premier déplacement. Une saisie déjà utilisée est
>   refusée (409) avec le nom de la ruche et du rucher qui la porte ;
> - le **NAPI** est le numéro d'*apiculteur* : il identifie le propriétaire
>   auprès de l'administration, et **toutes ses ruches le partagent**. Aucune
>   unicité n'est donc contrôlée dessus.
>
> Les deux champs peuvent rester vides.
>
> **Déplacement** : la ruche emporte tout son historique (visites, traitements,
> récoltes) et son numéro. Seule sa position sur le plan est effacée — elle
> désignait un emplacement sur la photo du rucher d'origine. L'opération est
> tracée au journal avec l'origine et la destination.

### Visites

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter les visites | ✅ | ✅ | ✅ | ✅ | ✅ |
| Saisir une visite | ✅ | 🔶 ¹ | ✅ | 🔶 ¹ | ⛔ |
| Modifier **sa propre** visite | ✅ | ✅ | ✅ | ✅ | ⛔ |
| Modifier la visite **d'un autre** | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Supprimer une visite (n'importe laquelle) | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Planifier ses visites (météo) | ✅ | ✅ | ✅ | ✅ | ✅ |

¹ `_check_hive_access` (saisie) : admin et yard_manager passent partout ; les
autres doivent être **gestionnaires de la ruche** concernée.

> **Modifier une visite ne suit pas la même règle que la saisir.** Une visite
> est l'observation d'une personne à un instant donné : son auteur la corrige
> librement, même sur une ruche dont il n'a pas la charge. Retoucher celle d'un
> autre revient à réécrire son témoignage — c'est donc réservé aux
> administrateurs, et la correction est inscrite au journal comme telle. Le
> responsable de rucher, qui pouvait auparavant modifier les visites d'autrui
> sur ses ruches, ne le peut plus.
>
> La **suppression** reste administrateur uniquement, y compris pour sa propre
> visite : effacer une observation fait disparaître une trace du suivi du
> cheptel, ce n'est pas une correction de saisie.

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

L'inventaire distingue le matériel **de l'association** (propriété non
renseignée) du matériel **personnel** d'un adhérent.

| Action | admin | treasurer | yard_manager | user | readonly |
|---|:--:|:--:|:--:|:--:|:--:|
| Consulter le stock de l'association | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consulter le matériel personnel d'un tiers | ✅ | ⛔ ¹ | ✅ | ⛔ | ⛔ |
| Créer / modifier un article **de l'association** | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Créer / modifier **son propre** matériel | ✅ | ✅ | ✅ | ✅ | ⛔ ² |
| Modifier le matériel personnel d'un tiers | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Entrée / sortie sur un article de l'association | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Entrée / sortie sur **son propre** matériel | ✅ | ✅ | ✅ | ✅ | ⛔ ² |
| Déplacer un article de l'association | ✅ | ✅ | ✅ | ⛔ | ⛔ |
| Supprimer un article de l'association | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Supprimer **son propre** matériel | ✅ | ✅ | ✅ | ✅ | ⛔ ² |
| Attribuer la **propriété** à un tiers | ✅ | ✅ | ✅ | ⛔ | ⛔ |

¹ Le trésorier gère le stock de l'association mais n'est pas « responsable de
cheptel » : la lecture du matériel personnel suit la même règle que le miel
privé (propriétaire + admin + responsable de rucher).

² Le compte en lecture seule n'écrit rien, y compris sur ses propres données.

> Le matériel personnel d'un adhérent n'est **pas** visible des autres
> adhérents — ni dans la liste, ni dans les alertes de stock, ni dans le résumé
> par emplacement. Un adhérent ne peut ni le céder à l'association, ni
> l'attribuer à quelqu'un d'autre.

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
| Déclarer une perte sur une récolte (fond de cuve) | ✅ | ⛔ | ✅ | 🔶 ⁴ | ⛔ |
| Corriger le stock d'un lot de pots (casse) | ✅ | ⛔ | ✅ | 🔶 ⁴ | ⛔ |

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
| Créer / modifier un compte | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Désactiver un compte | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Supprimer un compte | 🔶 ⁵ | ⛔ | ⛔ | ⛔ | ⛔ |
| Attribuer les rôles | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Réinitialiser le mot de passe d'un tiers | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Changer **son propre** mot de passe | ✅ | ✅ | ✅ | ✅ | ✅ |
| Modifier **ses propres** coordonnées (e-mail, téléphone) | ✅ | ✅ | ✅ | ✅ | ✅ ³ |
| Demander un lien « mot de passe oublié » | 🔓 | 🔓 | 🔓 | 🔓 | 🔓 |
| Changer **son** rôle actif / par défaut | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ | 🔶 ¹ |
| Import CSV de comptes | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Lire les critères météo | ✅ | ✅ | ✅ | ✅ | ✅ |
| Régler **ses propres** critères météo | ✅ | ✅ | ✅ | ✅ | ✅ ³ |
| Régler les critères **de l'association** | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Signaler un problème sur une ruche | ✅ | ✅ | ✅ | ✅ | ⛔ |
| Diagnostic des notifications | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Lire le journal des versions | ✅ | ✅ | ✅ | ✅ | ✅ |
| Lire / vider **sa propre** boîte de notifications | ✅ | ✅ | ✅ | ✅ | ✅ ³ |
| Documentation : écrire / supprimer | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Notifications : s'abonner, régler ses préférences | ✅ | ✅ | ✅ | ✅ | ✅ |

⁴ Uniquement sur ses propres récoltes et lots privés.

🔓 Accessible **sans être connecté** : c'est tout l'objet de la fonctionnalité.

³ Ces réglages ne concernent que son propre compte ou son propre écran : ils
font partie des rares écritures autorisées à un compte en lecture seule, au
même titre que son mot de passe.

### Mot de passe oublié — choix de sécurité

| Point | Mise en œuvre |
|---|---|
| Enumération des comptes | La réponse est **identique** que le compte existe ou non ; sans cela le formulaire servirait d'annuaire des adhérents. |
| Stockage du jeton | Seule l'**empreinte SHA-256** est conservée : une fuite de la base ne permet pas de rejouer un lien encore valide. |
| Durée de vie | 1 heure, **usage unique**. Valider une demande révoque toutes les autres en cours pour ce compte. |
| Abus | Au plus 5 demandes par heure et par compte, et jamais deux à moins d'une minute d'intervalle. |
| Après réinitialisation | `token_version` est incrémenté : **tous les appareils sont déconnectés**, ce qui est le comportement attendu si le mot de passe était compromis. |
| Compte désactivé ou sans adresse | Aucun envoi, réponse neutre, trace côté serveur pour l'administrateur. |
| SMTP non configuré | Message explicite invitant à passer par un administrateur : laisser attendre un e-mail qui ne partira jamais serait pire. |

### Supprimer ou désactiver un compte

⁵ Un compte ne se supprime que s'il **n'a rien laissé derrière lui**. Une visite,
une récolte, une vente, un acte au registre sanitaire, une écriture de
trésorerie, un mouvement de stock ou du matériel personnel décrivent la vie de
l'association : ils doivent survivre au départ de la personne **et** conserver
leur auteur. La suppression est donc refusée en nommant précisément ce qui la
retient, et l'interface propose à la place de **désactiver** le compte —
la personne ne peut plus se connecter, tout son historique reste en place.

`GET /api/users/{id}/deletion-check` renvoie cet état avant toute action, pour
que la boîte de dialogue propose d'emblée le bon bouton plutôt que de laisser
se heurter à une erreur de base de données.

Sont également refusés : la suppression de **son propre** compte et celle du
**dernier administrateur**. Une ruche qui perdrait son seul responsable est
signalée en avertissement, sans bloquer.

> **Adresse e-mail et identifiant sont deux choses distinctes.** La colonne
> `users.email` porte l'**identifiant de connexion** (« paulin ») pour des
> raisons historiques ; l'adresse réelle vit dans `users.contact_email`. Une
> adresse ne peut désigner qu'un seul compte, sinon la réinitialisation
> viserait le mauvais adhérent.

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
