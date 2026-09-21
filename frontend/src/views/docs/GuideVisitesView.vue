<template>
  <DocPage
    eyebrow="Guide — chapitre 3"
    title="Visiter ses ruches"
    lead="Le Mode Live sur le terrain, la visite rapide, l'historique, les corrections et les alertes."
    intro="C'est le cœur de l'application : ce qui est saisi ici alimente le tableau de bord, le suivi sanitaire et les bilans. L'écran de visite est conçu pour être utilisé <b>avec des gants, au soleil, sans réseau</b>."
    :sections="sections"
    :prev="{ title: 'Chapitre 2 — Ruchers et ruches', to: { name: 'docs-guide-ruchers' } }"
    :next="{ title: 'Chapitre 4 — Miellée, sanitaire, stocks', to: { name: 'docs-guide-gestion' } }"
  />
</template>

<script setup>
import DocPage from '../../components/DocPage.vue'

const sections = [
  {
    id: 'lancer', t: 'Lancer une visite',
    blocks: [
      { p: "Deux portes d'entrée, selon ce que vous allez faire :" },
      { table: { head: ['Pour…', 'Où cliquer'], rows: [
        ['Faire le tour de <b>vos</b> ruches, tous ruchers confondus', "Le bouton <b>« Visite rapide de mes ruches »</b> sur le tableau de bord — ou l'onglet <b>Visite rapide</b> (icône abeille) en bas de l'écran sur téléphone."],
        ['Visiter <b>tout un rucher</b>', "Ruchers → ouvrez le rucher → bouton <b>Mode Live</b>."],
      ] } },
      { p: "Dans les deux cas, la même interface s'ouvre et enchaîne les ruches une par une." },
      { img: 'g-visite-rapide.jpg', cap: "L'écran de visite (Mode Live)." },
    ],
  },
  {
    id: 'prefill', t: 'Les valeurs de la dernière visite sont reprises',
    blocks: [
      { p: "Pour chaque ruche, le formulaire s'ouvre <b>pré-rempli avec les valeurs de la dernière visite</b> : nombre de hausses, cadres de corps, couvain, réserves, nourrissement. Vous ne corrigez que ce qui a changé — le plus souvent, deux ou trois chiffres." },
      { p: "Un bandeau en haut de l'écran rappelle d'où viennent ces valeurs : <i>« Valeurs reprises de la visite du … par … »</i>. Une ruche jamais visitée démarre, elle, avec des valeurs neutres." },
      { tip: "Ce rappel évite l'erreur classique du retour de terrain : remettre 0 hausse sur une ruche qui en a deux, simplement parce que le champ était vide." },
    ],
  },
  {
    id: 'date', t: 'Saisir une visite faite un autre jour',
    blocks: [
      { p: "On rentre du rucher le soir, ou le lendemain, et on saisit la tournée au calme. Sans rien faire, la visite serait datée du moment de la saisie — et l'historique de la colonie s'en trouverait faussé." },
      { p: "L'application distingue donc <b>deux dates</b> :" },
      { table: { head: ['Date', 'Qui la pose', 'Modifiable ?'], rows: [
        ['<b>Date de la visite</b>', "Vous. Pré-remplie au jour même.", "✅ à la saisie et après coup"],
        ['<b>Date de saisie</b>', "L'application, automatiquement.", "❌ jamais — c'est la trace du moment où l'information est entrée"],
      ] } },
      { h3: 'Changer la date pendant la tournée' },
      { steps: [
        "Dans la visite rapide, sous le sélecteur de ruche, touchez la pastille <b>« Visite d'aujourd'hui »</b>.",
        "Choisissez la date à laquelle la visite a réellement eu lieu.",
        "Touchez <b>Fermer</b>. La pastille passe en <b>orange</b> et un bandeau rappelle la date retenue.",
        "Saisissez vos observations normalement.",
      ] },
      { img: 'g-visite-date.jpg', cap: "La date se change d'un geste, et l'avertissement reste visible." },
      { note: "La date choisie vaut pour <b>toutes les ruches de la tournée</b> : on ne la saisit qu'une fois. Le bouton <b>Aujourd'hui</b> la ramène au jour même." },
      { tip: "Le jour même, l'heure réelle est conservée — elle situe la visite dans la journée. Pour un jour passé, l'application retient midi : prétendre connaître l'heure d'une visite d'hier serait faux." },
      { h3: 'Corriger la date après coup' },
      { steps: [
        "Ouvrez l'<b>historique des visites</b> et cliquez sur le <b>crayon</b> de la ligne concernée.",
        "En tête du formulaire, corrigez <b>Date de la visite</b>.",
        "Cliquez sur <b>Enregistrer</b>.",
      ] },
      { p: "Dans l'historique, la date de saisie s'affiche en petit sous la date de visite, <b>uniquement lorsqu'elle diffère</b> — « saisie le 21/09/26 ». Les visites saisies le jour même n'affichent rien de plus." },
      { warn: "Une date <b>dans le futur est refusée</b>, à la saisie comme à la correction. Et la date de saisie ne se modifie jamais : c'est elle qui atteste de l'ordre réel des enregistrements." },
    ],
  },
  {
    id: 'saisie', t: 'Remplir une visite, champ par champ',
    blocks: [
      { h3: 'Hausses' },
      { p: "Un gros <b>−</b> et un gros <b>+</b> de part et d'autre du chiffre. Un appui = une hausse. Aucun clavier ne s'ouvre." },
      { h3: 'Corps' },
      { ul: [
        "<b>Corps ouvert</b> — l'interrupteur du haut. <b>Laissez-le fermé si vous n'avez pas ouvert le corps</b> : couvain et réserves passent alors en <code>N/A</code> au lieu d'enregistrer un faux zéro.",
        "<b>Cadres de corps</b> — le même compteur <b>−</b> / <b>+</b> que les hausses.",
        "<b>Reine</b> — deux gros boutons : <b>Vue</b> (vert) ou <b>Non vue</b> (rouge).",
        "<b>Couvain</b> et <b>Réserves</b> — deux curseurs de <b>0 à 9</b>, à faire glisser. 0 = rien, 9 = plein.",
      ] },
      { h3: 'Nourrissement' },
      { p: "Un bouton par option : <b>Aucun</b>, <b>Sirop 50/50</b>, <b>Sirop 70/30</b>, <b>Candi</b>, <b>Pâte protéinée</b>." },
      { h3: 'Alerte' },
      { p: "Le grand bouton <b>« Pas d'alerte »</b> bascule en <b>« ALERTE ACTIVÉE »</b> (rouge) d'un appui. Utilisez-le pour tout ce qui demande un retour : colonie faible, reine perdue, dégât matériel." },
      { h3: 'Commentaire' },
      { p: "Zone de texte libre, avec <b>dictée vocale</b> : appuyez sur l'icône <b>microphone</b> et parlez, le texte s'écrit tout seul. Ce que le micro comprend s'affiche en direct — pratique avec des gants." },
      { h3: 'Passer à la ruche suivante' },
      { steps: [
        "Cliquez sur <b>Enregistrer</b> : la visite part et la ruche suivante s'affiche.",
        "Les flèches <b>‹</b> et <b>›</b> en bas permettent de revenir en arrière ou de sauter une ruche.",
        "Quand toutes les ruches sont passées, l'écran affiche <b>« Visite terminée ! »</b>.",
      ] },
      { note: "Pendant la visite, un bouton <b>Historique</b> montre les dernières visites de la ruche en cours : utile pour comparer avec le mois dernier sans quitter l'écran." },
    ],
  },
  {
    id: 'hors-ligne', t: 'Travailler sans réseau',
    blocks: [
      { p: "Au milieu des champs, le réseau manque souvent. L'application continue de fonctionner : les visites sont <b>gardées dans le téléphone</b> et envoyées automatiquement dès que la connexion revient." },
      { steps: [
        "Saisissez normalement : rien ne change à l'écran.",
        "De retour en zone couverte, une <b>icône nuage avec un chiffre</b> apparaît dans la barre du haut : c'est le nombre de visites en attente.",
        "L'envoi se fait tout seul ; pour le forcer, cliquez sur cette icône.",
      ] },
      { warn: "Ne désinstallez pas l'application et ne videz pas les données du navigateur tant que le compteur n'est pas revenu à zéro : les visites en attente seraient perdues." },
    ],
  },
  {
    id: 'historique', t: "L'historique des visites",
    blocks: [
      { steps: ["Menu de gauche → <b>Historique des visites</b> (sur téléphone : onglet <b>Historique visites</b> en bas)."] },
      { p: "Un tableau de toutes les visites : date, ruche, reine, couvain, réserves, hausses, alerte, commentaire, auteur." },
      { img: 'g-visites.jpg', cap: "L'historique des visites." },
    ],
  },
  {
    id: 'filtres', t: 'Filtrer et trier',
    blocks: [
      { p: "Un bandeau <b>Filtres</b> surmonte le tableau. Les filtres se <b>combinent</b> : on peut ne garder que les visites d'une ruche <i>et</i> d'un auteur donné." },
      { img: 'g-filtres.jpg', cap: 'La barre de filtres (agrandie).' },
      { table: { head: ['Filtre', 'Effet'], rows: [
        ['<b>Ruche</b>', "N'affiche que l'historique de cette ruche."],
        ['<b>Auteur</b>', 'Les visites saisies par une personne.'],
        ['<b>Alerte</b>', '<i>Avec alerte</i> ou <i>Sans alerte</i>.'],
        ['<b>Dans le commentaire</b>', 'Recherche un mot dans le texte libre.'],
      ] } },
      { steps: [
        "Déroulez le filtre voulu et choisissez une valeur.",
        "Le compteur à droite indique combien de lignes restent (« 12 visites sur 148 »).",
        "Cliquez sur <b>Réinitialiser</b> pour tout effacer d'un coup.",
        "Pour <b>trier</b>, cliquez sur l'<b>en-tête d'une colonne</b> : un second clic inverse l'ordre.",
      ] },
      { note: "La même barre de filtres se retrouve sur la miellée, le sanitaire, l'inventaire, la trésorerie, le journal et les adhérents : le geste est partout identique." },
    ],
  },
  {
    id: 'corriger', t: 'Corriger ou supprimer une visite',
    blocks: [
      { p: "Une erreur de saisie se corrige, elle n'a pas à rester dans l'historique." },
      { table: { head: ['Vous êtes…', 'Vous pouvez…'], rows: [
        ['<b>Adhérent</b>', "Modifier <b>vos propres</b> visites. Le crayon n'apparaît que sur vos lignes."],
        ['<b>Administrateur</b>', "Modifier <b>et supprimer</b> n'importe quelle visite. L'opération est inscrite au journal."],
      ] } },
      { steps: [
        "Dans l'historique, repérez la ligne à corriger.",
        "Cliquez sur l'icône <b>crayon</b>, à droite de la ligne.",
        "Corrigez les champs, puis <b>Enregistrer</b>.",
        "Pour supprimer (administrateur), cliquez sur la <b>corbeille</b> et confirmez.",
      ] },
      { img: 'g-visite-modif.jpg', cap: "Correction d'une visite." },
    ],
  },
  {
    id: 'alerte', t: 'Signaler un problème',
    blocks: [
      { p: "Hors visite — un passage devant le rucher, un appel d'un voisin — le <b>triangle rouge</b> de la barre du haut permet d'alerter depuis n'importe quel écran. Deux types de signalement sont proposés en haut de la fenêtre." },
      { table: { head: ['Type', 'Pour quoi', 'Qui est prévenu'], rows: [
        ['<b>Sur une ruche</b>', "Ce qui concerne une colonie : toit envolé, agressivité, entrée obstruée, peu d'activité au trou de vol.", "Les <b>responsables de cette ruche</b>. Le signalement est ajouté à l'<b>historique de la ruche</b> et aux <b>Alertes actives</b> du tableau de bord."],
        ['<b>Général</b>', "Ce qui ne concerne aucune colonie : clôture, chemin d'accès, matériel commun, voisinage, point à passer au bureau.", "Les <b>administrateurs</b> et les <b>responsables de rucher</b>. <b>Rien n'est écrit dans l'historique d'une ruche.</b>"],
      ] } },
      { img: 'g-signaler.jpg', cap: "Signaler un problème sur une ruche." },
      { h3: 'Signaler un problème sur une ruche' },
      { steps: [
        "Cliquez sur le <b>triangle rouge</b> ⚠ en haut de l'écran.",
        "Laissez le type sur <b>Sur une ruche</b>.",
        "Choisissez la <b>ruche concernée</b> dans la liste.",
        "Décrivez le problème dans <b>« Que se passe-t-il ? »</b> — soyez concret : « toit envolé », « peu d'activité au trou de vol ».",
        "Cliquez sur <b>Envoyer l'alerte</b>.",
      ] },
      { p: "L'alerte apparaît ensuite dans <b>Alertes actives</b> sur le tableau de bord, jusqu'à ce qu'elle soit traitée." },
      { h3: 'Signalement général' },
      { steps: [
        "Cliquez sur le <b>triangle rouge</b> ⚠, puis sur <b>Général</b>.",
        "Choisissez éventuellement le <b>rucher concerné</b> — laissez vide si cela touche l'association en général.",
        "Décrivez la situation, puis cliquez sur <b>Envoyer le signalement</b>.",
      ] },
      { img: 'g-signaler-general.jpg', cap: 'Un signalement général.' },
      { note: "Un encadré rappelle, avant l'envoi, <b>qui sera prévenu</b>. En désignant un rucher, les responsables de ses ruches le sont en plus du bureau : ce sont eux qui sont sur place." },
      { tip: "Un signalement général n'entre dans l'historique d'aucune colonie : le suivi des ruches reste propre, et le message arrive quand même à qui de droit." },
    ],
  },
]
</script>
