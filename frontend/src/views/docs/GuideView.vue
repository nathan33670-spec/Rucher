<template>
  <DocArticle
    eyebrow="Prise en main"
    title="Guide complet de l'application"
    lead="Six chapitres illustrés, du premier écran de connexion à l'administration."
  >
    <v-alert type="info" variant="tonal" density="comfortable" class="mb-6">
      Le guide est écrit pour quelqu'un qui <b>n'a jamais utilisé l'application</b> :
      chaque manipulation est décrite pas à pas, avec l'endroit exact où cliquer.
      Les captures proviennent de l'application ; certains écrans ne sont
      visibles que selon votre rôle.
    </v-alert>

    <v-row class="mb-2">
      <v-col v-for="c in chapitres" :key="c.n" cols="12" sm="6">
        <v-card :to="c.to" class="h-100" variant="tonal" color="primary" hover>
          <v-card-item>
            <template v-slot:prepend>
              <v-avatar color="primary" size="38" class="font-weight-bold">{{ c.n }}</v-avatar>
            </template>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ c.t }}</v-card-title>
          </v-card-item>
          <v-card-text class="pt-0">
            <p class="mb-2">{{ c.d }}</p>
            <div class="text-caption text-medium-emphasis">{{ c.items }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <h2>Par où commencer ?</h2>
    <ul>
      <li><b>Vous venez de recevoir vos identifiants</b> : chapitre 1, puis chapitre 3 avant votre première visite.</li>
      <li><b>Vous partez au rucher</b> : le <RouterLink :to="{ name: 'docs-memo' }">mémo rapide</RouterLink> tient en une page.</li>
      <li><b>Vous montez le rucher dans l'application</b> : chapitre 2.</li>
      <li><b>Vous créez les comptes des adhérents</b> : chapitre 6, section « Importer les adhérents par fichier CSV ».</li>
    </ul>

    <h2>Le vocabulaire de l'application</h2>
    <v-table density="compact" class="mb-4">
      <thead><tr><th>Terme</th><th>Ce qu'il désigne</th></tr></thead>
      <tbody>
        <tr v-for="m in lexique" :key="m[0]"><td v-html="m[0]"></td><td v-html="m[1]"></td></tr>
      </tbody>
    </v-table>
  </DocArticle>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import DocArticle from '../../components/DocArticle.vue'

const chapitres = [
  { n: 1, t: 'Premiers pas', to: { name: 'docs-guide-premiers-pas' },
    d: "Se connecter, comprendre l'écran, installer l'application sur son téléphone.",
    items: "Connexion · Mot de passe oublié · Barre du haut · Menu · Rôles · Installation" },
  { n: 2, t: 'Ruchers et ruches', to: { name: 'docs-guide-ruchers' },
    d: "Créer un rucher, y ajouter des ruches, les numéroter et les placer sur le plan.",
    items: "Numéro de ruche · NAPI · Plan · Déplacer une ruche · Photos" },
  { n: 3, t: 'Visiter ses ruches', to: { name: 'docs-guide-visites' },
    d: "Le Mode Live sur le terrain, l'historique, les corrections et les alertes.",
    items: "Visite rapide · Hors-ligne · Filtres · Corriger une visite · Signaler" },
  { n: 4, t: 'Miellée, sanitaire, stocks', to: { name: 'docs-guide-gestion' },
    d: "Récoltes et pots, traitements et comptages, matériel, recettes et dépenses.",
    items: "Récolte · Mise en pot · Pertes · Varroa · Inventaire · Trésorerie" },
  { n: 5, t: 'Notifications, météo, événements', to: { name: 'docs-guide-suivi' },
    d: "Être prévenu au bon moment, choisir son créneau, répondre aux sorties.",
    items: "Cloche · Notifications push · Critères météo · Participation" },
  { n: 6, t: 'Administration', to: { name: 'docs-guide-admin' },
    d: "Comptes, import CSV des adhérents, réglages de l'association, journal.",
    items: "Créer un compte · Format du fichier CSV · SMTP · Journal" },
]

const lexique = [
  ['<b>Rucher</b>', "Le lieu où sont posées les ruches."],
  ['<b>Ruche</b>', "Une colonie. Elle porte un <b>numéro</b> que vous choisissez, unique dans l'application."],
  ['<b>N° NAPI</b>', "Le numéro d'apiculteur du propriétaire — le même pour toutes ses ruches. À ne pas confondre avec le numéro de ruche."],
  ['<b>Visite</b>', "Un passage devant une ruche : état du couvain, des réserves, des hausses, commentaire."],
  ['<b>Mode Live</b>', "L'écran de saisie terrain, qui enchaîne les ruches une par une."],
  ['<b>Alerte</b>', "Un problème signalé sur une ruche, qui notifie ses responsables."],
  ['<b>Miellée</b>', "Le suivi du miel : récoltes en kg, pots, ventes, pertes."],
  ['<b>Rôle</b>', "Ce que vous avez le droit de faire : administrateur, responsable de rucher, trésorier, usager, lecture seule."],
]
</script>
