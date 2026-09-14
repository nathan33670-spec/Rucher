<template>
  <DocPage
    eyebrow="Guide — chapitre 2"
    title="Ruchers et ruches"
    lead="Créer un rucher, y ajouter des ruches, les numéroter, les placer sur le plan, les déplacer."
    intro="Un <b>rucher</b> est un lieu ; une <b>ruche</b> est une colonie posée dans ce lieu. Tout part de l'onglet <b>Ruchers</b> du menu de gauche."
    :sections="sections"
    :prev="{ title: 'Chapitre 1 — Premiers pas', to: { name: 'docs-guide-premiers-pas' } }"
    :next="{ title: 'Chapitre 3 — Visiter ses ruches', to: { name: 'docs-guide-visites' } }"
  />
</template>

<script setup>
import DocPage from '../../components/DocPage.vue'

const sections = [
  {
    id: 'liste', t: 'La liste des ruchers',
    blocks: [
      { steps: ["Dans le menu de gauche, section <b>Suivi du rucher</b>, cliquez sur <b>Ruchers</b>."] },
      { p: "Chaque rucher est une carte : son nom, son adresse, le nombre de ruches et l'état général. Un clic sur la carte ouvre son détail." },
      { img: 'g-ruchers.jpg', cap: 'La liste des ruchers.' },
      { h3: 'Créer un rucher' },
      { steps: [
        "Cliquez sur <b>Nouveau rucher</b>, en haut à droite de l'écran.",
        "Donnez-lui un <b>nom</b> parlant (« Verger du Moulin »), une <b>adresse</b>, et éventuellement ses coordonnées.",
        "Cliquez sur <b>Enregistrer</b>.",
      ] },
      { note: "Créer, modifier ou supprimer un rucher demande le rôle <b>responsable de rucher</b> ou <b>administrateur</b>. Si le bouton n'apparaît pas, c'est que votre rôle ne le permet pas." },
    ],
  },
  {
    id: 'detail', t: "Le détail d'un rucher",
    blocks: [
      { p: "Le détail réunit tout ce qui concerne le lieu : le plan des ruches, la liste des colonies, leur dernière visite et leur état sanitaire." },
      { img: 'g-rucher-detail.jpg', cap: "Détail d'un rucher." },
      { ul: [
        "<b>Mode Live</b> — lance une visite terrain enchaînant les ruches de ce rucher (chapitre 3).",
        "<b>Ajouter une photo aérienne</b> — la photo sert de fond au plan.",
        "<b>Nouvelle ruche</b> — ajoute une colonie.",
      ] },
    ],
  },
  {
    id: 'ruche', t: 'Ajouter une ruche',
    blocks: [
      { steps: [
        "Depuis le détail du rucher, cliquez sur <b>Nouvelle ruche</b>.",
        "Remplissez le formulaire (détail des champs ci-dessous).",
        "Cliquez sur <b>Enregistrer</b>.",
      ] },
      { img: 'g-ruche-form.jpg', cap: "Le formulaire d'une ruche." },
      { table: { head: ['Champ', 'À quoi il sert'], rows: [
        ['<b>N° de ruche</b>', "Le numéro que <b>vous</b> choisissez et qui est peint sur la ruche. C'est lui qui <b>identifie la colonie partout dans l'application</b>. <b>Deux ruches ne peuvent pas porter le même</b>, et il est modifiable à tout moment."],
        ['<b>Nom</b>', "Facultatif, un surnom qui vient <b>en complément</b> du numéro : « 12 — La bleue »."],
        ['<b>N° NAPI (apiculteur)</b>', "Le numéro d'apiculteur du <b>propriétaire</b> : le même pour toutes ses ruches. Il n'a pas à être unique."],
        ['<b>Associatif / Privé</b>', "À qui appartient la colonie. Le privé reste visible, mais distingué dans les bilans."],
        ['<b>Statut</b>', "<code>active</code> (en production), <code>inactive</code> (vide, en réserve) ou <code>dead</code> (colonie morte)."],
        ['<b>Responsables</b>', "Les adhérents qui suivent cette ruche. Ce sont eux qui reçoivent les alertes la concernant, et elle apparaît dans leur « Visite rapide »."],
        ['<b>Notes</b>', 'Origine de la reine, particularités, rappels.'],
      ] } },
      { warn: "<b>Le n° de ruche et le n° NAPI sont deux choses différentes.</b> Le premier identifie <i>cette</i> colonie ; le second identifie l'<i>apiculteur</i> et se répète sur tout son cheptel." },
    ],
  },
  {
    id: 'numero', t: 'Changer le numéro d\'une ruche',
    blocks: [
      { p: "Renumérotation du rucher, ruche repeinte, erreur de saisie : le numéro se corrige sans rien perdre de l'historique." },
      { steps: [
        "Ouvrez le rucher, puis cliquez sur l'icône <b>crayon</b> de la ruche concernée.",
        "Modifiez le <b>premier champ</b>, <b>N° de ruche</b>.",
        "Cliquez sur <b>Enregistrer</b>.",
      ] },
      { p: "Le changement est <b>immédiat et visible partout</b> : plan du rucher, écran de visite, historique, suivi sanitaire, miellée." },
      { note: "Si le numéro est déjà pris, un message rouge s'affiche <b>sous le champ</b> et rien n'est enregistré : corrigez le numéro et réessayez. L'application indique quelle ruche le porte déjà." },
      { warn: "Ne confondez pas avec le <b>N° NAPI</b>, juste en dessous : celui-là identifie l'<i>apiculteur</i> et se répète sur toutes ses ruches. Le modifier ne change pas le numéro de la colonie." },
      { tip: "Les ruches créées avant cette fonctionnalité ont reçu un numéro automatiquement au premier démarrage : celles qui portaient déjà un repère l'ont conservé, les autres ont reçu le premier numéro libre. Tous sont modifiables ici." },
    ],
  },
  {
    id: 'plan', t: 'Le plan : placer les ruches',
    blocks: [
      { p: "Le plan reproduit l'implantation réelle : sur le terrain, on retrouve la bonne ruche d'un coup d'œil, sans compter les rangs." },
      { steps: [
        "Ajoutez d'abord une <b>photo aérienne</b> du rucher si vous en avez une : elle sert de fond.",
        "<b>Attrapez</b> une ruche avec la souris (ou le doigt sur téléphone) et <b>faites-la glisser</b> à sa place.",
        "Relâchez : la position est enregistrée <b>immédiatement</b>, il n'y a pas de bouton à valider.",
      ] },
      { img: 'g-plan.jpg', cap: 'Le plan des ruches (agrandi).' },
      { tip: "La couleur d'une ruche sur le plan résume son état : elle change quand une alerte est en cours." },
    ],
  },
  {
    id: 'deplacer', t: "Déplacer une ruche vers un autre rucher",
    blocks: [
      { p: "Transhumance ou réorganisation : la ruche change de lieu en emportant <b>tout son historique</b> — visites, traitements, récoltes." },
      { steps: [
        "Ouvrez le rucher de départ.",
        "Sur la ruche, cliquez sur l'icône <b>double flèche</b> (<b>Déplacer la ruche</b>).",
        "Choisissez le <b>rucher de destination</b> dans la liste déroulante.",
        "Cliquez sur <b>Déplacer</b>.",
      ] },
      { img: 'g-ruche-deplacer.jpg', cap: 'Déplacer une ruche.' },
      { note: "Sa <b>position sur le plan est effacée</b> : elle désignait un emplacement sur la photo de l'ancien rucher. Replacez-la sur le nouveau plan." },
    ],
  },
  {
    id: 'photo', t: 'Photos',
    blocks: [
      { ul: [
        "<b>Photo aérienne du rucher</b> : fond du plan. Bouton <b>Ajouter une photo aérienne</b> en haut du détail.",
        "<b>Photo d'une ruche</b> : utile pour garder trace d'un cadre, d'une reine marquée ou d'un dégât.",
      ] },
      { tip: "Sur téléphone, le bouton photo ouvre directement l'appareil : inutile de prendre la photo à part puis de la retrouver." },
    ],
  },
]
</script>
