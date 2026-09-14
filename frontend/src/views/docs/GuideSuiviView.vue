<template>
  <DocPage
    eyebrow="Guide — chapitre 5"
    title="Notifications, météo et événements"
    lead="Être prévenu au bon moment, choisir le bon jour pour visiter, répondre aux sorties."
    intro="Trois écrans qui font gagner du temps : la <b>cloche</b> pour ne rien manquer, la <b>météo</b> pour choisir son créneau, les <b>événements</b> pour la vie de l'association."
    :sections="sections"
    :prev="{ title: 'Chapitre 4 — Miellée, sanitaire, stocks', to: { name: 'docs-guide-gestion' } }"
    :next="{ title: 'Chapitre 6 — Administration', to: { name: 'docs-guide-admin' } }"
  />
</template>

<script setup>
import DocPage from '../../components/DocPage.vue'

const sections = [
  {
    id: 'cloche', t: 'La cloche : vos notifications',
    blocks: [
      { p: "La <b>cloche</b> de la barre du haut réunit tout ce qui vous a été adressé : alertes sur vos ruches, nouvelles visites, mouvements de matériel, événements, et les <b>nouveautés de l'application</b> à chaque mise à jour." },
      { steps: [
        "Cliquez sur la <b>cloche</b> 🔔 en haut à droite. Une <b>pastille rouge</b> indique le nombre de messages non lus.",
        "Cliquez sur un message pour l'ouvrir : s'il renvoie vers un écran (une ruche, un événement), l'application vous y emmène directement.",
        "<b>Tout marquer comme lu</b> efface la pastille ; <b>Tout effacer</b> vide la liste.",
      ] },
      { img: 'g-cloche.jpg', cap: 'Le panneau des notifications.' },
      { note: "La cloche fonctionne <b>même si les notifications push sont désactivées</b> : les messages restent consultables ici. Le push ne fait qu'ajouter l'avertissement sur l'écran du téléphone." },
    ],
  },
  {
    id: 'push', t: 'Recevoir les notifications sur son téléphone',
    blocks: [
      { p: "Une notification « push » s'affiche sur le téléphone même quand l'application est fermée. L'activation vous est proposée au premier lancement ; elle se règle ensuite à tout moment." },
      { steps: [
        "Menu de gauche → section <b>Réglages</b> → <b>Notifications</b>.",
        "Basculez l'interrupteur <b>« Activer les notifications »</b>. Le navigateur demande votre autorisation : répondez <b>Autoriser</b>.",
        "Choisissez ensuite, catégorie par catégorie, ce que vous voulez recevoir.",
        "Cliquez sur <b>« Envoyer une notification de test »</b> pour vérifier qu'elle arrive bien sur cet appareil.",
      ] },
      { img: 'g-notifications.jpg', cap: "L'écran Notifications." },
      { table: { head: ['Catégorie', 'Vous prévient quand…'], rows: [
        ['<b>Événements</b>', 'Une sortie ou une réunion est annoncée.'],
        ['<b>Nouvelle visite</b>', 'Une visite est saisie.'],
        ['<b>Mouvement de matériel</b>', 'Entrée, sortie ou déplacement en inventaire.'],
        ['<b>Alerte terrain</b>', 'Un problème est signalé sur une ruche.'],
        ['<b>Sanitaire</b>', 'Un traitement ou un comptage varroa est enregistré.'],
        ['<b>Trésorerie</b>', 'Une écriture est passée.'],
      ] } },
      { warn: "Le réglage vaut <b>pour cet appareil</b>. Si vous utilisez l'application sur un téléphone <i>et</i> un ordinateur, activez-la sur les deux." },
      { h3: "Rien n'arrive ?" },
      { ul: [
        "<b>iPhone / iPad</b> : l'application doit être <b>installée sur l'écran d'accueil</b> (chapitre 1). Dans le navigateur Safari seul, Apple n'autorise aucune notification.",
        "<b>Android</b> : vérifiez que les notifications ne sont pas bloquées pour le site, dans les réglages du navigateur.",
        "Vérifiez que la catégorie concernée est bien activée, puis relancez le <b>test</b>.",
      ] },
    ],
  },
  {
    id: 'meteo', t: 'Météo : choisir le bon créneau',
    blocks: [
      { p: "Ouvrir une ruche par temps froid, humide ou venteux stresse la colonie et se paie en piqûres. L'écran <b>Météo</b> classe chaque jour des 7 prochains en <b>Idéal</b>, <b>Correct</b> ou <b>Déconseillé</b>, et propose les <b>heures</b> les plus favorables." },
      { img: 'g-meteo.jpg', cap: "L'écran Météo." },
      { h3: 'Régler ses propres critères' },
      { p: "Chacun a son matériel, ses disponibilités et sa tolérance au vent : les critères sont <b>personnels</b>." },
      { steps: [
        "Menu de gauche → <b>Météo</b>.",
        "Cliquez sur <b>Mes critères</b>, en haut à droite du bandeau.",
        "Réglez la <b>plage horaire</b>, la <b>température mini et maxi</b>, la <b>pluie maxi</b> (%) et le <b>vent maxi</b> (km/h) pour le niveau <b>Idéal</b>, puis les seuils plus larges du niveau <b>Correct</b>.",
        "Indiquez combien d'<b>heures idéales</b> sont requises pour qu'une journée entière soit classée « Idéale ».",
        "<b>Enregistrer</b> : l'affichage se recalcule aussitôt, pour vous seul.",
      ] },
      { note: "Un administrateur dispose en plus du bouton <b>Critères de l'association</b> : ce sont les valeurs par défaut, appliquées à qui n'a pas réglé les siennes." },
      { tip: "Depuis un jour favorable, un administrateur peut créer directement une <b>sortie</b> : le créneau est pré-rempli avec les bonnes heures." },
    ],
  },
  {
    id: 'evenements', t: 'Événements de l\'association',
    blocks: [
      { p: "Sorties, réunions, journées de récolte : l'onglet <b>Événements</b> les présente en <b>« À venir »</b> et <b>« Passés »</b>." },
      { img: 'g-evenements.jpg', cap: "L'écran Événements." },
      { h3: 'Dire si vous venez' },
      { steps: [
        "Menu de gauche → <b>Événements</b>.",
        "Sur la carte de l'événement, cliquez sur <b>Je viens</b>, <b>Peut-être</b> ou <b>Absent</b>.",
        "Votre réponse est enregistrée immédiatement et reste <b>modifiable</b> jusqu'au jour J.",
      ] },
      { h3: 'Mettre la date dans son agenda' },
      { steps: [
        "Cliquez sur le bouton <b>Calendrier</b> de l'événement.",
        "Choisissez <b>Apple / Android (.ics)</b> ou <b>Google Agenda</b> : la date se place dans votre agenda habituel, avec le lieu.",
      ] },
      { h3: 'Créer un événement' },
      { p: "Réservé aux <b>administrateurs</b> et aux <b>responsables de rucher</b>." },
      { steps: [
        "Cliquez sur <b>Nouvel événement</b>.",
        "Renseignez l'<b>intitulé</b>, la <b>date</b>, les <b>horaires</b>, le <b>lieu</b> et la <b>description</b>.",
        "Indiquez s'il est <b>public</b> (visible de tous les adhérents) ou <b>privé</b> (visible des seuls administrateurs).",
        "Enregistrez. La <b>liste des participants</b> est ensuite consultable sur la carte de l'événement.",
      ] },
      { h3: 'Relancer : envoyer une notification sur les téléphones' },
      { p: "Une annonce faite trois semaines à l'avance se perd. Le bouton <b>Notifier</b> envoie une nouvelle notification quand vous le décidez : la veille d'une sortie, ou pour un détail de dernière minute." },
      { steps: [
        "Sur la carte de l'événement, cliquez sur <b>Notifier</b>.",
        "Relisez l'encadré : il dit <b>à qui</b> la notification va partir.",
        "Écrivez un <b>message</b> si vous le souhaitez — « rendez-vous 9h au parking », « pensez à votre combinaison ». Laissé vide, le message reprend la date, le lieu et l'invitation à répondre.",
        "Cliquez sur <b>Envoyer la notification</b>.",
      ] },
      { img: 'g-evenement-notifier.jpg', cap: "Relancer une notification sur un événement." },
      { table: { head: ['Vous êtes…', 'Vous pouvez notifier…'], rows: [
        ["<b>L'organisateur</b> de l'événement", "Le vôtre, même si vous n'êtes pas administrateur."],
        ['<b>Administrateur</b>', "N'importe quel événement."],
        ['<b>Adhérent</b>', "Le bouton n'apparaît pas."],
      ] } },
      { note: "Un événement <b>privé</b> n'étant visible que des administrateurs, seuls eux en sont notifiés — le notifier à tous en dévoilerait le contenu." },
      { tip: "La fenêtre rappelle la <b>date du dernier envoi</b> : on voit d'un coup d'œil si quelqu'un a déjà relancé, et les adhérents ne reçoivent pas tout en double." },
    ],
  },
]
</script>
