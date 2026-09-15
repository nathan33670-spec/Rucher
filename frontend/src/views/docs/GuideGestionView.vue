<template>
  <DocPage
    eyebrow="Guide — chapitre 4"
    title="Miellée, sanitaire, inventaire, trésorerie"
    lead="Récoltes et pots, traitements et comptages varroa, matériel, recettes et dépenses."
    intro="Ces quatre écrans forment la partie <b>Gestion</b> du menu. Ils partagent la même logique : une liste filtrable, un bouton <b>Nouveau…</b> en haut à droite, un crayon pour corriger."
    :sections="sections"
    :prev="{ title: 'Chapitre 3 — Visiter ses ruches', to: { name: 'docs-guide-visites' } }"
    :next="{ title: 'Chapitre 5 — Notifications, météo, événements', to: { name: 'docs-guide-suivi' } }"
  />
</template>

<script setup>
import DocPage from '../../components/DocPage.vue'

const sections = [
  {
    id: 'miellee', t: 'Miellée : de la récolte au pot vendu',
    blocks: [
      { p: "L'écran <b>Miellée</b> suit le miel sur toute sa route : ce qui est <b>récolté</b> (en kg), ce qui est <b>mis en pot</b>, ce qui est <b>vendu</b>, et ce qui est <b>perdu</b>." },
      { img: 'g-miellee.jpg', cap: "L'écran Miellée." },
      { h3: '1. Enregistrer une récolte' },
      { steps: [
        "Cliquez sur <b>Nouvelle récolte</b>.",
        "Renseignez la <b>catégorie de miel</b> (printemps, toutes fleurs…), le <b>rucher</b>, la <b>quantité en kg</b> pesée, le <b>nombre de hausses et de cadres</b>, et la <b>date</b>.",
        "<b>Enregistrer</b>.",
      ] },
      { h3: '2. Mettre en pot' },
      { steps: [
        "Cliquez sur <b>Mise en pot</b>.",
        "Choisissez la <b>récolte source</b> (le lot d'où vient le miel), le <b>format du pot</b> (250 g, 500 g…), le <b>nombre de pots</b> et le <b>prix unitaire</b>.",
        "<b>Enregistrer</b> : le « reste à empoter » de la récolte diminue d'autant.",
      ] },
      { note: "Si la quantité empotée dépasse la récolte, un avertissement rouge s'affiche : c'est presque toujours une erreur de saisie de kg ou de format de pot." },
      { h3: '3. Vendre' },
      { steps: [
        "Cliquez sur <b>Vente de miel</b>.",
        "Choisissez le <b>pot à vendre</b>, la <b>quantité</b>, le <b>prix unitaire</b> et éventuellement l'<b>acheteur</b>.",
        "<b>Enregistrer</b> : le stock baisse et la recette remonte dans la trésorerie.",
      ] },
      { tip: "Les ruches privées sont suivies séparément. Le sélecteur <b>« Voir les données privées de… »</b>, en haut, permet à un responsable de consulter la miellée privée d'un adhérent." },
    ],
  },
  {
    id: 'perte', t: 'Déclarer une perte de miel (fond de cuve)',
    blocks: [
      { p: "Une partie du miel n'arrive jamais en pot : fond de cuve, filtre, maturateur renversé. <b>La récolte reste enregistrée telle qu'elle a été pesée</b> — seul le « reste à empoter » diminue. Les kilos réellement produits ne sont donc pas falsifiés." },
      { steps: [
        "Dans le tableau des <b>récoltes</b>, repérez la ligne concernée.",
        "Cliquez sur l'icône <b>goutte barrée</b> (<b>Déclarer une perte</b>).",
        "Saisissez la <b>quantité perdue en kg</b>.",
        "Choisissez un <b>motif</b> dans la liste — <i>Fond de cuve</i>, <i>Filtre et maturateur</i>, <i>Renversement</i>, <i>Cristallisation inexploitable</i>, <i>Consommation personnelle</i> — ou tapez le vôtre.",
        "<b>Enregistrer</b>.",
      ] },
      { img: 'g-miel-perte.jpg', cap: 'Déclarer une perte sur une récolte.' },
      { tip: "Trop déclaré ? Saisissez une quantité <b>négative</b> : cela corrige la perte au lieu d'en ajouter une." },
    ],
  },
  {
    id: 'ajuster', t: "Corriger le stock de pots d'un lot",
    blocks: [
      { p: "Casse, don, écart constaté en rangeant la réserve : on corrige le nombre de pots réellement présents. L'écart est enregistré comme une <b>perte, jamais comme une vente</b> — les comptes restent justes." },
      { steps: [
        "Dans le tableau des <b>pots</b>, cliquez sur <b>Ajuster</b> sur la ligne du lot.",
        "Saisissez le <b>nombre de pots réellement en stock</b> (le nombre compté, pas l'écart).",
        "Choisissez un <b>motif</b> : <i>Casse</i>, <i>Don</i>, <i>Écart d'inventaire</i>, <i>Dégustation</i>, ou le vôtre.",
        "<b>Enregistrer</b>.",
      ] },
      { img: 'g-miel-ajuster.jpg', cap: "Correction du stock d'un lot de pots." },
    ],
  },
  {
    id: 'sanitaire', t: 'Sanitaire : traitements et comptages varroa',
    blocks: [
      { p: "Deux onglets en haut de l'écran : <b>Traitements</b> et <b>Comptages</b>. C'est la trace exigée par le registre d'élevage." },
      { img: 'g-sanitaire.jpg', cap: "L'écran Sanitaire." },
      { h3: 'Enregistrer un traitement' },
      { steps: [
        "Onglet <b>Traitements</b> → bouton <b>Nouveau traitement</b>.",
        "Sélectionnez les <b>ruches concernées</b> — plusieurs à la fois, ce qui évite de ressaisir dix fois le même traitement.",
        "Renseignez le <b>type</b> (ex. <i>Anti-varroa</i>), le <b>produit</b> (ex. <i>Apivar</i>), le <b>dosage</b> (ex. <i>2 lanières</i>), la <b>date de début</b> et la <b>date de fin</b>.",
        "<b>Enregistrer</b>.",
      ] },
      { h3: 'Enregistrer un comptage varroa' },
      { steps: [
        "Onglet <b>Comptages</b> → <b>Nouveau comptage</b>.",
        "Sélectionnez les <b>ruches</b>, la <b>date</b>, et le <b>nombre de varroas par jour</b>.",
        "Précisez la <b>méthode</b> dans les notes (ex. <i>lange graissé 3 jours</i>, <i>lavage à l'alcool</i>).",
      ] },
      { note: "Pour savoir quoi faire de ces chiffres, voyez la page <b>Le varroa</b> de la documentation : seuils d'intervention et périodes de traitement." },
    ],
  },
  {
    id: 'inventaire', t: 'Inventaire du matériel',
    blocks: [
      { p: "Le matériel de l'association : hausses, cadres, cire, pots vides, enfumoirs. Avec un <b>seuil d'alerte</b> par article, pour ne plus découvrir la veille d'une récolte qu'il manque des pots." },
      { img: 'g-inventaire.jpg', cap: "L'écran Inventaire." },
      { h3: 'Ajouter un article' },
      { steps: [
        "Cliquez sur <b>Nouvel article</b>.",
        "Renseignez le <b>nom</b>, la <b>catégorie</b>, l'<b>emplacement</b> (local, remorque…), la <b>quantité</b>, l'<b>unité</b> et le <b>prix unitaire</b>.",
        "Fixez un <b>seuil d'alerte</b> : en dessous, l'article remonte dans « Stocks bas » sur le tableau de bord.",
        "Choisissez la <b>propriété</b> : matériel de l'association ou matériel personnel.",
      ] },
      { h3: 'Entrées, sorties, déplacements' },
      { ul: [
        "<b>Entrée</b> — un achat, un don : la quantité augmente.",
        "<b>Sortie</b> — du matériel consommé ou cassé : la quantité baisse. Indiquez toujours un <b>motif</b>.",
        "<b>Déplacer</b> — le même matériel change d'emplacement, sans changer de quantité.",
      ] },
      { tip: "<b>Inventaire personnel</b> : un article marqué « personnel » n'appartient qu'à vous. Vous le voyez et le gérez, les autres adhérents non." },
    ],
  },
  {
    id: 'tresorerie', t: 'Trésorerie',
    blocks: [
      { p: "Recettes et dépenses de l'association, avec les <b>factures</b> jointes et le bilan annuel. Écran réservé au <b>trésorier</b> et à l'<b>administrateur</b> — un administrateur peut l'ouvrir en lecture à tous depuis la configuration." },
      { img: 'g-tresorerie.jpg', cap: "L'écran Trésorerie." },
      { steps: [
        "Cliquez sur <b>Nouvelle écriture</b>.",
        "Choisissez le <b>type</b> : <b>Recette</b> ou <b>Dépense</b>.",
        "Choisissez la <b>catégorie</b>, saisissez le <b>montant en euros</b>, le <b>fournisseur</b> et une <b>description</b>.",
        "Utilisez <b>Joindre une facture</b> pour téléverser le justificatif (photo ou PDF) : il restera attaché à l'écriture.",
        "<b>Enregistrer</b>.",
      ] },
      { tip: "Prenez la facture en photo au moment de l'achat et joignez-la tout de suite : c'est une demi-journée de retrouvailles de papiers en moins à la clôture." },
    ],
  },
  {
    id: 'sumup', t: 'Liaison avec SumUp',
    blocks: [
      { p: "La trésorerie peut se remplir depuis votre compte SumUp, par deux chemins différents. Ce n'est pas un caprice de réglage : <b>l'API de SumUp est celle d'un encaisseur, pas d'une banque</b>." },
      { table: { head: ['Ce que vous voulez', 'Comment', 'Automatique ?'], rows: [
        ['<b>Recettes</b> (encaissements par carte)', "Bouton <b>Synchroniser SumUp</b>", "✅ Oui, d'un clic"],
        ['<b>Dépenses</b> (achats avec la carte du compte pro)', "Bouton <b>Importer un relevé</b> (fichier CSV)", "❌ Non — SumUp n'expose pas le compte professionnel"],
        ['<b>Factures SumUp Invoice</b>', "À joindre à la main dans l'application", "❌ Non — SumUp Invoice n'a pas d'API"],
      ] } },
      { img: 'g-tresorerie-sumup.jpg', cap: 'La trésorerie après une synchronisation SumUp.' },
      { h3: '1. Enregistrer la clé (une seule fois)' },
      { steps: [
        "Dans votre <b>tableau de bord SumUp</b>, ouvrez <b>Développeurs → Clés d'API</b> et créez une clé avec la portée <b>« transactions.history »</b>.",
        "Dans l'application : menu <b>Réglages → Configuration</b>, section <b>Liaison SumUp</b>.",
        "Collez la clé, laissez le <b>code marchand</b> vide (il est demandé à SumUp automatiquement), puis <b>Enregistrer</b>.",
      ] },
      { img: 'g-sumup-reglages.jpg', cap: 'Les réglages de la liaison.' },
      { note: "La clé n'est <b>jamais réaffichée</b> : le champ reste vide et indique seulement qu'une clé est enregistrée. Le laisser vide en enregistrant conserve la clé en place." },
      { h3: '2. Récupérer les recettes' },
      { steps: [
        "Écran <b>Trésorerie</b> → bouton <b>Synchroniser SumUp</b>.",
        "Les encaissements deviennent des <b>recettes</b>, les remboursements des <b>dépenses</b> ; les paiements échoués sont ignorés.",
        "Un bandeau indique combien d'écritures ont été ajoutées et combien étaient déjà connues.",
      ] },
      { tip: "Cliquez autant de fois que vous voulez : chaque écriture garde la référence SumUp dont elle provient, une seconde synchronisation ne recrée donc rien." },
      { h3: '3. Récupérer les dépenses' },
      { steps: [
        "Dans votre tableau de bord SumUp, téléchargez le <b>relevé du compte</b> au format <b>CSV</b> (pas PDF).",
        "Écran <b>Trésorerie</b> → bouton <b>Importer un relevé</b> → choisissez le fichier.",
        "Les montants <b>négatifs</b> deviennent des dépenses, les positifs des recettes.",
        "Joignez ensuite les <b>factures</b> aux dépenses concernées, avec le trombone.",
      ] },
      { note: "Les en-têtes du relevé sont reconnus en français comme en anglais, avec point-virgule, virgule ou tabulation, et une colonne <i>Montant</i> signée ou deux colonnes <i>Débit</i> / <i>Crédit</i>. Si le fichier n'est pas reconnu, le message d'erreur <b>liste les colonnes trouvées</b> — transmettez-la pour qu'on ajoute le format." },
      { tip: "Réimporter le même relevé, ou un relevé qui chevauche le précédent, ne crée aucun doublon. Vous pouvez donc importer chaque mois sans faire attention aux dates." },
      { h3: 'Reconnaître une écriture importée' },
      { p: "Une petite <b>flèche circulaire</b> apparaît à côté de la date des écritures venues de SumUp. Les écritures saisies à la main n'en portent pas." },
      { warn: "La liaison est réservée aux rôles <b>trésorier</b> et <b>administrateur</b>, comme le reste de l'écriture en trésorerie." },
    ],
  },
]
</script>
