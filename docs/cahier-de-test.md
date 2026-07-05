# 📋 Cahier de Test — Rucher Manager

> **Version** : 1.0 — 12 mai 2026
> **Saison apicole simulée** : Mars → Septembre 2026
> **URL locale** : http://127.0.0.1:7080
> **Comptes de test** :

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | admin@rucher.local | admin1234 |
| Responsable rucher | marie@rucher.local | test1234 |
| Responsable rucher | jean@rucher.local | test1234 |
| Trésorier | sophie@rucher.local | test1234 |
| Adhérent simple | lucie@rucher.local | test1234 |
| Adhérent simple | antoine@rucher.local | test1234 |
| Adhérent simple | thomas@rucher.local | test1234 |
| Adhérent simple | emilie@rucher.local | test1234 |

---

## 📦 Données de référence

### Ruchers (3)
| Nom | Localisation | Nb ruches asso | Nb ruches privées |
|-----|-------------|----------------|-------------------|
| Rucher des Lavandes | Montagne | 5 | 2 |
| Rucher du Littoral | Bord de mer | 5 | 2 |
| Rucher de la Forêt | Forêt | 5 | 1 |

### Catégories de miel
- Toutes fleurs
- Châtaignier
- Maquis
- Acacia
- Lavande

---

## 🔐 Module 1 — Authentification & Autorisations

### TC-1.1 — Connexion admin
| | |
|---|---|
| **Précondition** | Application démarrée, base initialisée |
| **Action** | Se connecter avec `admin@rucher.local` / `admin1234` |
| **Résultat attendu** | Redirection vers le tableau de bord. Menu complet visible (dont Trésorerie, Utilisateurs) |
| **Statut** | ⬜ |

### TC-1.2 — Connexion adhérent simple
| | |
|---|---|
| **Précondition** | TC-1.1 exécuté (utilisateurs créés) |
| **Action** | Se connecter avec `lucie@rucher.local` / `test1234` |
| **Résultat attendu** | Redirection dashboard. Menu visible : Tableau de bord, Ruchers, Visites, Inventaire, Miellée, Sanitaire, Journal. **PAS** de Trésorerie ni Utilisateurs |
| **Statut** | ⬜ |

### TC-1.3 — Connexion trésorier
| | |
|---|---|
| **Action** | Se connecter avec `sophie@rucher.local` / `test1234` |
| **Résultat attendu** | Menu avec Trésorerie visible. Pas d'onglet Utilisateurs |
| **Statut** | ⬜ |

### TC-1.4 — Connexion mot de passe erroné
| | |
|---|---|
| **Action** | Se connecter avec `admin@rucher.local` / `mauvais` |
| **Résultat attendu** | Message d'erreur "Email ou mot de passe incorrect" |
| **Statut** | ⬜ |

### TC-1.5 — Déconnexion
| | |
|---|---|
| **Précondition** | Connecté |
| **Action** | Cliquer sur "Déconnexion" dans le menu latéral |
| **Résultat attendu** | Redirection vers /login, token supprimé du localStorage |
| **Statut** | ⬜ |

### TC-1.6 — Navigation simple clic
| | |
|---|---|
| **Précondition** | Connecté |
| **Action** | Cliquer une seule fois sur chaque élément du menu latéral |
| **Résultat attendu** | Navigation immédiate à la page correspondante sans besoin de double-clic |
| **Statut** | ⬜ |

---

## 🏕️ Module 2 — Gestion des Ruchers

### TC-2.1 — Lister les ruchers
| | |
|---|---|
| **Précondition** | Connecté (tout rôle) |
| **Action** | Naviguer vers "Ruchers" |
| **Résultat attendu** | 3 ruchers affichés avec nom, localisation et nombre de ruches |
| **Statut** | ⬜ |

### TC-2.2 — Créer un rucher (admin)
| | |
|---|---|
| **Précondition** | Connecté en admin |
| **Action** | Cliquer "Nouveau rucher", saisir nom + localisation, valider |
| **Résultat attendu** | Rucher ajouté à la liste |
| **Statut** | ⬜ |

### TC-2.3 — Détail d'un rucher
| | |
|---|---|
| **Action** | Cliquer sur "Rucher des Lavandes" |
| **Résultat attendu** | Page détail avec liste des ruches (5 asso + 2 privées), chips ownership (bleu/orange) |
| **Statut** | ⬜ |

### TC-2.4 — Créer une ruche
| | |
|---|---|
| **Précondition** | Page détail d'un rucher, connecté admin |
| **Action** | Cliquer "Ajouter une ruche", saisir nom + type ownership |
| **Résultat attendu** | Ruche ajoutée avec le bon chip de couleur |
| **Statut** | ⬜ |

### TC-2.5 — Lancer une visite live depuis le détail rucher
| | |
|---|---|
| **Action** | Cliquer "Démarrer visite" sur la page détail |
| **Résultat attendu** | Redirection vers `/visits/live/{apiaryId}`, première ruche active affichée |
| **Statut** | ⬜ |

---

## 📋 Module 3 — Visites

### TC-3.1 — Quick button visite depuis le dashboard
| | |
|---|---|
| **Précondition** | Connecté, dashboard affiché |
| **Action** | Cliquer sur le bouton d'un rucher dans "Saisie rapide de visite" |
| **Résultat attendu** | Navigation vers le mode live pour ce rucher |
| **Statut** | ⬜ |

### TC-3.2 — Mode live : section Hausses
| | |
|---|---|
| **Précondition** | Mode live actif, ruche affichée |
| **Action** | Utiliser les boutons +/- pour modifier le nombre de hausses |
| **Résultat attendu** | Compteur incrémente/décrémente. Ne descend pas en dessous de 0 |
| **Statut** | ⬜ |

### TC-3.3 — Mode live : section Corps (corps ouvert)
| | |
|---|---|
| **Précondition** | Mode live, switch "Corps ouvert" activé |
| **Action** | Sélectionner reine vue, ajuster couvain (slider 0-9), ajuster réserves (slider 0-9) |
| **Résultat attendu** | Les 3 champs sont interactifs et affichent les valeurs |
| **Statut** | ⬜ |

### TC-3.4 — Mode live : section Corps (corps non ouvert)
| | |
|---|---|
| **Précondition** | Mode live, switch "Corps ouvert" désactivé |
| **Action** | Vérifier l'affichage |
| **Résultat attendu** | Couvain et Réserves affichent "N/A — corps non ouvert". Sliders masqués |
| **Statut** | ⬜ |

### TC-3.5 — Mode live : enregistrer et passer à la suivante
| | |
|---|---|
| **Action** | Remplir le formulaire et cliquer "Suivante" |
| **Résultat attendu** | Snackbar ✅, progression avance, formulaire réinitialisé, ruche suivante affichée |
| **Statut** | ⬜ |

### TC-3.6 — Mode live : bouton "Passer"
| | |
|---|---|
| **Précondition** | Mode live, pas la dernière ruche |
| **Action** | Cliquer "Passer" |
| **Résultat attendu** | Passe à la ruche suivante **sans enregistrer** de visite. Formulaire réinitialisé |
| **Statut** | ⬜ |

### TC-3.7 — Mode live : bouton Précédent
| | |
|---|---|
| **Précondition** | Mode live, ruche 2 ou plus |
| **Action** | Cliquer ◀ |
| **Résultat attendu** | Retour à la ruche précédente, formulaire réinitialisé |
| **Statut** | ⬜ |

### TC-3.8 — Mode live : dernière ruche → Terminer
| | |
|---|---|
| **Précondition** | Dernière ruche du rucher |
| **Action** | Cliquer "Terminer" |
| **Résultat attendu** | Écran "Visite terminée !" avec nombre de ruches visitées et bouton retour |
| **Statut** | ⬜ |

### TC-3.9 — Mode live : nourrissement rapide
| | |
|---|---|
| **Action** | Sélectionner "Sirop 50/50" dans les boutons de nourrissement |
| **Résultat attendu** | Valeur sélectionnée visible, enregistrée à la sauvegarde |
| **Statut** | ⬜ |

### TC-3.10 — Mode live : alerte
| | |
|---|---|
| **Action** | Cliquer "Pas d'alerte" → le bouton passe en rouge "ALERTE ACTIVÉE" |
| **Résultat attendu** | Alerte activée. Après sauvegarde, la visite apparaît en alerte dans le tableau |
| **Statut** | ⬜ |

### TC-3.11 — Mode live : dictée vocale
| | |
|---|---|
| **Précondition** | Navigateur supportant Web Speech API |
| **Action** | Cliquer "Dictée vocale", parler en français |
| **Résultat attendu** | Texte transcrit dans le champ commentaire |
| **Statut** | ⬜ |

### TC-3.12 — Mode live : sélecteur de ruche
| | |
|---|---|
| **Action** | Utiliser le sélecteur déroulant en haut pour sauter directement à la ruche 4 |
| **Résultat attendu** | Navigation directe à la ruche choisie |
| **Statut** | ⬜ |

### TC-3.13 — Onglet Visites : pas de bouton création
| | |
|---|---|
| **Action** | Naviguer vers "Visites" |
| **Résultat attendu** | Tableau des visites affiché. **Pas** de bouton "Nouvelle visite". Chip indiquant "Saisie depuis le tableau de bord" |
| **Statut** | ⬜ |

### TC-3.14 — Onglet Visites : modifier une visite existante
| | |
|---|---|
| **Action** | Cliquer ✏️ sur une visite existante |
| **Résultat attendu** | Dialog de modification avec 2 sections (Hausses / Corps). Modification enregistrée |
| **Statut** | ⬜ |

### TC-3.15 — Onglet Visites : supprimer (admin uniquement)
| | |
|---|---|
| **Précondition** | Connecté admin |
| **Action** | Cliquer 🗑 sur une visite |
| **Résultat attendu** | Confirmation demandée, visite supprimée |
| **Statut** | ⬜ |

---

## 🍯 Module 4 — Miellée (Production)

### TC-4.1 — Accès miellée — Adhérent simple
| | |
|---|---|
| **Précondition** | Connecté avec `lucie@rucher.local` (rôle user) |
| **Action** | Naviguer vers "Miellée" |
| **Résultat attendu** | Page accessible. Boutons "Nouvelle récolte", "Mise en pot", "Nouvelle vente" visibles |
| **Statut** | ⬜ |

### TC-4.2 — Créer une récolte privée — Adhérent simple
| | |
|---|---|
| **Précondition** | Connecté `lucie@rucher.local` |
| **Action** | Cliquer "Nouvelle récolte". Vérifier que le toggle "Associatif" est **désactivé/grisé**. Sélectionner "Privé", saisir 5 kg, valider |
| **Résultat attendu** | Récolte créée avec ownership "Privé" |
| **Statut** | ⬜ |

### TC-4.3 — Interdiction récolte associative — Adhérent simple
| | |
|---|---|
| **Précondition** | Connecté `lucie@rucher.local` |
| **Action** | Tenter de forcer une récolte associative (via API ou si toggle activable) |
| **Résultat attendu** | Erreur 403 "Seuls les responsables peuvent gérer les récoltes associatives" |
| **Statut** | ⬜ |

### TC-4.4 — Créer une récolte associative — Responsable
| | |
|---|---|
| **Précondition** | Connecté `marie@rucher.local` (yard_manager) |
| **Action** | Nouvelle récolte → toggle "Associatif" activable → saisir 20 kg, catégorie "Toutes fleurs" |
| **Résultat attendu** | Récolte créée, chip "Asso" bleu dans le tableau |
| **Statut** | ⬜ |

### TC-4.5 — Créer une récolte privée — Responsable
| | |
|---|---|
| **Précondition** | Connecté `marie@rucher.local` |
| **Action** | Nouvelle récolte → toggle "Privé" → saisir 8 kg |
| **Résultat attendu** | Récolte créée, chip "Privé" orange |
| **Statut** | ⬜ |

### TC-4.6 — Modifier une récolte
| | |
|---|---|
| **Action** | Cliquer ✏️ sur une récolte existante, modifier la quantité |
| **Résultat attendu** | Quantité mise à jour dans le tableau |
| **Statut** | ⬜ |

### TC-4.7 — Supprimer une récolte (admin uniquement)
| | |
|---|---|
| **Précondition** | Connecté admin |
| **Action** | Cliquer 🗑 sur une récolte |
| **Résultat attendu** | Suppression après confirmation |
| **Statut** | ⬜ |

### TC-4.8 — Filtre par ownership (onglets)
| | |
|---|---|
| **Action** | Cliquer sur les onglets "Tout" / "Associatif" / "Privé" |
| **Résultat attendu** | Le tableau, le stock de pots et les ventes se filtrent selon l'ownership sélectionné |
| **Statut** | ⬜ |

---

## 🫙 Module 5 — Mise en pot

### TC-5.1 — Créer un lot de pots — Adhérent (privé)
| | |
|---|---|
| **Précondition** | Connecté `lucie@rucher.local`, au moins une récolte privée existante |
| **Action** | Cliquer "Mise en pot" → sélectionner récolte privée, format 500g, quantité 10, prix 8€ |
| **Résultat attendu** | Lot créé. Stock de pots mis à jour dans la section dédiée |
| **Statut** | ⬜ |

### TC-5.2 — Interdiction mise en pot asso — Adhérent
| | |
|---|---|
| **Action** | Tenter de mettre en pot une récolte avec ownership "associative" |
| **Résultat attendu** | Toggle "Asso" grisé côté UI. Si forcé via API → 403 |
| **Statut** | ⬜ |

### TC-5.3 — Créer un lot de pots — Responsable (asso)
| | |
|---|---|
| **Précondition** | Connecté `marie@rucher.local` |
| **Action** | Mise en pot d'une récolte asso, format 250g, quantité 20, prix 5€ |
| **Résultat attendu** | Stock affiché avec chip "🏛️" bleu |
| **Statut** | ⬜ |

### TC-5.4 — Vérifier stock de pots
| | |
|---|---|
| **Action** | Vérifier la section "Stock de pots" |
| **Résultat attendu** | Cartes par format/ownership avec quantité restante et vendus |
| **Statut** | ⬜ |

---

## 💰 Module 6 — Ventes de miel

### TC-6.1 — Vendre des pots privés — Adhérent
| | |
|---|---|
| **Précondition** | Connecté `lucie@rucher.local`, pots privés en stock |
| **Action** | Cliquer "Nouvelle vente" → sélectionner pot privé, quantité 3, acheteur "Jean" |
| **Résultat attendu** | Vente enregistrée. Stock décrémenté. Transaction créée en compta |
| **Statut** | ⬜ |

### TC-6.2 — Interdiction vente pots asso — Adhérent
| | |
|---|---|
| **Précondition** | Connecté `lucie@rucher.local` |
| **Action** | Tenter de vendre un pot associatif (sélectionner un pot asso dans la liste) |
| **Résultat attendu** | Erreur 403 côté API |
| **Statut** | ⬜ |

### TC-6.3 — Vendre des pots asso — Trésorier
| | |
|---|---|
| **Précondition** | Connecté `sophie@rucher.local` (treasurer) |
| **Action** | Vente de 5 pots asso 500g |
| **Résultat attendu** | Vente OK. Transaction INCOME créée automatiquement avec catégorie HONEY_SALE |
| **Statut** | ⬜ |

### TC-6.4 — Stock insuffisant
| | |
|---|---|
| **Action** | Tenter de vendre plus de pots que le stock disponible |
| **Résultat attendu** | Erreur "Stock insuffisant (X disponibles)" |
| **Statut** | ⬜ |

### TC-6.5 — Tableau des ventes
| | |
|---|---|
| **Action** | Vérifier le tableau des ventes |
| **Résultat attendu** | Colonnes : Date, Type (Asso/Privé), Format, Qté, P.U., Total, Acheteur |
| **Statut** | ⬜ |

---

## 📊 Module 7 — Dashboard & Statistiques

### TC-7.1 — Stats rapides
| | |
|---|---|
| **Action** | Vérifier le dashboard |
| **Résultat attendu** | 4 cartes : Ruchers (3), Ruches (20), Visites (mois), Alertes |
| **Statut** | ⬜ |

### TC-7.2 — Stats miellée sur le dashboard
| | |
|---|---|
| **Action** | Vérifier la section "Production de miel" sur le dashboard |
| **Résultat attendu** | Cartes : production totale (kg), nb récoltes, détail par ownership (Asso/Privé), par catégorie, graphe mensuel |
| **Statut** | ⬜ |

### TC-7.3 — Alertes actives
| | |
|---|---|
| **Précondition** | Au moins une visite avec alerte |
| **Action** | Vérifier la section "Alertes actives" |
| **Résultat attendu** | Liste des visites alertées avec message, ruche et date |
| **Statut** | ⬜ |

### TC-7.4 — Dernières visites
| | |
|---|---|
| **Action** | Vérifier le tableau "Dernières visites" |
| **Résultat attendu** | 5 dernières visites avec date, ruche, auteur, reine, couvain, réserves |
| **Statut** | ⬜ |

### TC-7.5 — Alertes stock
| | |
|---|---|
| **Précondition** | Articles d'inventaire sous le seuil |
| **Action** | Vérifier la section "Stocks bas" |
| **Résultat attendu** | Articles listés avec quantité actuelle / seuil |
| **Statut** | ⬜ |

### TC-7.6 — Quick buttons visite
| | |
|---|---|
| **Action** | Vérifier la section "Saisie rapide de visite" |
| **Résultat attendu** | 1 bouton par rucher avec nom et nombre de ruches. Clic → mode live |
| **Statut** | ⬜ |

---

## 💵 Module 8 — Trésorerie

### TC-8.1 — Accès trésorerie — Admin
| | |
|---|---|
| **Précondition** | Connecté admin |
| **Action** | Naviguer vers "Trésorerie" |
| **Résultat attendu** | Liste des transactions visible |
| **Statut** | ⬜ |

### TC-8.2 — Accès trésorerie — Trésorier
| | |
|---|---|
| **Précondition** | Connecté `sophie@rucher.local` |
| **Action** | Naviguer vers "Trésorerie" |
| **Résultat attendu** | Accès autorisé, liste affichée |
| **Statut** | ⬜ |

### TC-8.3 — Accès trésorerie — Adhérent simple → interdit
| | |
|---|---|
| **Précondition** | Connecté `lucie@rucher.local` |
| **Action** | Vérifier que le lien "Trésorerie" n'apparaît pas dans le menu |
| **Résultat attendu** | Lien absent du menu latéral |
| **Statut** | ⬜ |

### TC-8.4 — Créer une dépense
| | |
|---|---|
| **Action** | Nouvelle transaction type EXPENSE, catégorie EQUIPMENT, 150€ |
| **Résultat attendu** | Transaction créée, solde mis à jour |
| **Statut** | ⬜ |

### TC-8.5 — Vérifier transaction auto depuis vente miel
| | |
|---|---|
| **Précondition** | Vente de miel effectuée (TC-6.x) |
| **Action** | Vérifier dans la trésorerie |
| **Résultat attendu** | Transaction INCOME / HONEY_SALE avec montant correspondant et description de la vente |
| **Statut** | ⬜ |

---

## 📦 Module 9 — Inventaire

### TC-9.1 — Lister le stock
| | |
|---|---|
| **Action** | Naviguer vers "Inventaire" |
| **Résultat attendu** | Liste des articles avec nom, quantité, seuil d'alerte |
| **Statut** | ⬜ |

### TC-9.2 — Créer un article
| | |
|---|---|
| **Action** | Ajouter "Cadres Dadant" quantité 50, seuil 10 |
| **Résultat attendu** | Article ajouté |
| **Statut** | ⬜ |

### TC-9.3 — Modifier une quantité
| | |
|---|---|
| **Action** | Modifier la quantité d'un article existant |
| **Résultat attendu** | Quantité mise à jour |
| **Statut** | ⬜ |

### TC-9.4 — Alertes de stock bas
| | |
|---|---|
| **Action** | Mettre un article sous son seuil |
| **Résultat attendu** | Apparaît dans les alertes stock du dashboard |
| **Statut** | ⬜ |

---

## 🩺 Module 10 — Sanitaire

### TC-10.1 — Accéder au module sanitaire
| | |
|---|---|
| **Action** | Naviguer vers "Sanitaire" |
| **Résultat attendu** | Page sanitaire accessible |
| **Statut** | ⬜ |

### TC-10.2 — Créer un traitement
| | |
|---|---|
| **Action** | Enregistrer un traitement varroa sur une ruche |
| **Résultat attendu** | Traitement enregistré avec dates et produit |
| **Statut** | ⬜ |

---

## 👥 Module 11 — Gestion des utilisateurs

### TC-11.1 — Lister les utilisateurs (admin)
| | |
|---|---|
| **Précondition** | Connecté admin |
| **Action** | Naviguer vers "Utilisateurs" |
| **Résultat attendu** | 10 utilisateurs listés avec rôles |
| **Statut** | ⬜ |

### TC-11.2 — Créer un utilisateur
| | |
|---|---|
| **Action** | Créer un nouvel utilisateur avec rôle "user" |
| **Résultat attendu** | Utilisateur créé, peut se connecter |
| **Statut** | ⬜ |

### TC-11.3 — Modifier les rôles
| | |
|---|---|
| **Action** | Passer un utilisateur de "user" à "yard_manager" |
| **Résultat attendu** | Après reconnexion, le menu et les permissions changent |
| **Statut** | ⬜ |

### TC-11.4 — Accès utilisateurs — Non-admin → interdit
| | |
|---|---|
| **Précondition** | Connecté non-admin |
| **Action** | Vérifier que "Utilisateurs" n'est pas dans le menu |
| **Résultat attendu** | Lien absent |
| **Statut** | ⬜ |

---

## 🔄 Module 12 — Catégories de miel (Admin)

### TC-12.1 — Voir les catégories
| | |
|---|---|
| **Précondition** | Connecté admin |
| **Action** | Page Miellée → section "Catégories de miel (Admin)" en bas |
| **Résultat attendu** | Chips avec les 5 catégories de base |
| **Statut** | ⬜ |

### TC-12.2 — Ajouter une catégorie
| | |
|---|---|
| **Action** | Saisir "Bruyère" et cliquer "Ajouter" |
| **Résultat attendu** | Chip ajouté |
| **Statut** | ⬜ |

### TC-12.3 — Supprimer une catégorie
| | |
|---|---|
| **Action** | Cliquer ✕ sur "Bruyère" |
| **Résultat attendu** | Chip supprimé |
| **Statut** | ⬜ |

### TC-12.4 — Catégories non visibles pour non-admin
| | |
|---|---|
| **Précondition** | Connecté non-admin |
| **Action** | Page Miellée |
| **Résultat attendu** | Section "Catégories de miel (Admin)" absente |
| **Statut** | ⬜ |

---

## 📱 Module 13 — Mode hors-ligne & PWA

### TC-13.1 — Indicateur offline
| | |
|---|---|
| **Action** | Couper le réseau (mode avion ou DevTools → Offline) |
| **Résultat attendu** | Bannière "Mode hors-ligne" visible en mode live |
| **Statut** | ⬜ |

### TC-13.2 — Enregistrer une visite offline
| | |
|---|---|
| **Précondition** | Mode hors-ligne, mode live actif |
| **Action** | Saisir et enregistrer une visite |
| **Résultat attendu** | Visite sauvegardée localement (IndexedDB/localStorage) |
| **Statut** | ⬜ |

### TC-13.3 — Synchronisation au retour en ligne
| | |
|---|---|
| **Action** | Rétablir le réseau |
| **Résultat attendu** | Visites en attente synchronisées automatiquement |
| **Statut** | ⬜ |

---

## 📝 Module 14 — Journal d'audit

### TC-14.1 — Consulter les logs
| | |
|---|---|
| **Action** | Naviguer vers "Journal" |
| **Résultat attendu** | Liste chronologique des actions (create, update, delete) avec utilisateur, type et ID |
| **Statut** | ⬜ |

---

## 🔀 Scénarios transverses — Parcours complets

### TC-S1 — Parcours adhérent privé complet
| Étape | Action | Résultat |
|-------|--------|---------|
| 1 | Connexion `lucie@rucher.local` | Dashboard visible |
| 2 | Dashboard → Quick button "Rucher des Lavandes" | Mode live |
| 3 | Saisir visite ruche 1 (reine ✅, couvain 7, réserves 6, 1 hausse) | Sauvegardé |
| 4 | Passer ruche 2 | Ruche 3 affichée, aucune visite créée pour ruche 2 |
| 5 | Terminer | Écran succès |
| 6 | Naviguer vers Miellée | Page accessible |
| 7 | Nouvelle récolte → Privé, 5 kg | Créée |
| 8 | Mise en pot → 10 x 500g, 8€/pot | Créée |
| 9 | Vente → 3 pots, acheteur "Pierre" | Vente OK, stock = 7 |
| 10 | Tentative récolte Associative | **Interdit** (toggle grisé + 403) |
| 11 | Vérifier Trésorerie absente du menu | **Absent** |
| **Statut** | | ⬜ |

### TC-S2 — Parcours responsable rucher complet
| Étape | Action | Résultat |
|-------|--------|---------|
| 1 | Connexion `marie@rucher.local` | Dashboard avec quick buttons |
| 2 | Quick button → Visite live | Mode live OK |
| 3 | Visiter toutes les ruches (7) | 7 visites créées |
| 4 | Miellée → Récolte associative 25 kg Toutes fleurs | Créée |
| 5 | Mise en pot asso 40 x 500g, 10€ | Créée |
| 6 | Vente asso 5 pots | OK + transaction auto |
| 7 | Miellée → Récolte privée 8 kg | Créée |
| 8 | Dashboard → Stats miellée mises à jour | 33 kg au total |
| **Statut** | | ⬜ |

### TC-S3 — Parcours trésorier
| Étape | Action | Résultat |
|-------|--------|---------|
| 1 | Connexion `sophie@rucher.local` | Trésorerie visible dans le menu |
| 2 | Vérifier les transactions HONEY_SALE auto | Présentes |
| 3 | Créer cotisation INCOME 30€ | OK |
| 4 | Miellée → Vente pots asso | OK (trésorier autorisé) |
| 5 | Vérifier transaction auto créée | Présente |
| 6 | Tenter d'accéder à Utilisateurs | **Absent du menu** |
| **Statut** | | ⬜ |

### TC-S4 — Parcours admin complet
| Étape | Action | Résultat |
|-------|--------|---------|
| 1 | Connexion admin | Tout visible |
| 2 | Créer un rucher + 3 ruches | OK |
| 3 | Visite live | OK |
| 4 | Miellée → Récolte asso + privée | Tout accessible |
| 5 | Trésorerie → Toutes opérations | OK |
| 6 | Utilisateurs → Créer, modifier rôles | OK |
| 7 | Catégories miel → CRUD | OK |
| 8 | Supprimer une visite, une récolte | OK |
| 9 | Journal → Vérifier les traces | Actions tracées |
| **Statut** | | ⬜ |

---

## 📐 Matrice des permissions

| Fonctionnalité | Admin | Yard Manager | Treasurer | User | Readonly |
|----------------|:-----:|:------------:|:---------:|:----:|:--------:|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Quick button visite | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mode live visite | ✅ | ✅ | ✅ | ✅ | ❌ |
| Modifier visite | ✅ | ✅ | ✅ | ✅ | ❌ |
| Supprimer visite | ✅ | ❌ | ❌ | ❌ | ❌ |
| Récolte **asso** | ✅ | ✅ | ❌ | ❌ | ❌ |
| Récolte **privée** | ✅ | ✅ | ✅ | ✅ | ❌ |
| Pots asso | ✅ | ✅ | ❌ | ❌ | ❌ |
| Pots privés | ✅ | ✅ | ✅ | ✅ | ❌ |
| Vente pots asso | ✅ | ✅ | ✅ | ❌ | ❌ |
| Vente pots privés | ✅ | ✅ | ✅ | ✅ | ❌ |
| Trésorerie | ✅ | ❌ | ✅ | ❌ | ❌ |
| Catégories miel | ✅ | ❌ | ❌ | ❌ | ❌ |
| Gestion utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Inventaire | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sanitaire | ✅ | ✅ | ✅ | ✅ | ✅ |
| Journal | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🧪 Commande de rechargement des données de test

```bash
cd /Users/U51YP03/Documents/rucher
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d --build
sleep 8
python3 test_saison_apicole.py
```

---

## 📌 Notes pour la génération de use cases

Pour ajouter un nouveau module ou use case :

1. Ajouter une section `## Module N — Nom` avec description
2. Chaque test case suit le format :
   - **TC-N.X** — Titre
   - Précondition / Action / Résultat attendu / Statut (⬜/✅/❌)
3. Mettre à jour la **matrice des permissions** si de nouveaux rôles/fonctionnalités sont ajoutés
4. Ajouter un **scénario transverse** si le nouveau module impacte plusieurs modules
5. Si des données de test sont nécessaires, mettre à jour `test_saison_apicole.py`
