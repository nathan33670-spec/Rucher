<template>
  <DocArticle
    eyebrow="Prise en main"
    title="Guide complet de l'application"
    lead="Chaque écran de Rucher Manager, expliqué pas à pas et illustré."
  >
    <v-alert type="info" variant="tonal" density="comfortable" class="mb-6">
      Les captures proviennent de l'application. Certains menus (Trésorerie,
      Utilisateurs, Journal) ne sont visibles que selon votre rôle.
    </v-alert>

    <!-- Table des matières -->
    <v-card variant="tonal" class="mb-6 pa-2">
      <v-list density="compact" nav>
        <v-list-item v-for="(s, i) in toc" :key="i" :href="'#' + s.id" :title="(i + 1) + '. ' + s.t" />
      </v-list>
    </v-card>

    <section v-for="s in sections" :key="s.id" :id="s.id" class="mb-8">
      <h2>{{ s.t }}</h2>
      <p v-for="(p, i) in s.p" :key="i" v-html="p"></p>
      <ul v-if="s.li">
        <li v-for="(l, i) in s.li" :key="i" v-html="l"></li>
      </ul>
      <figure v-if="s.img">
        <img :src="'/docs-img/' + s.img" :alt="s.t" loading="lazy" />
        <figcaption>{{ s.cap || s.t }}</figcaption>
      </figure>
    </section>
  </DocArticle>
</template>

<script setup>
import { computed } from 'vue'
import DocArticle from '../../components/DocArticle.vue'

const sections = [
  {
    id: 'accueil', t: "Page d'accueil publique",
    p: ["À l'adresse du site, une page grand public présente l'association et la protection des abeilles. Le bouton <b>« Accéder à l'application »</b> (en haut à droite et au centre) mène à la connexion."],
    img: 'accueil.jpg',
  },
  {
    id: 'connexion', t: 'Connexion',
    p: ['Saisissez votre <b>identifiant</b> (un nom simple ou un email, fourni par un administrateur) et votre <b>mot de passe</b>, puis <b>Se connecter</b>.'],
    li: ['Depuis un téléphone, un bouton <b>« Ajouter à l\'écran d\'accueil »</b> permet d\'installer l\'app.', 'Mot de passe oublié ? Un administrateur peut le réinitialiser.'],
    img: 'login.jpg',
  },
  {
    id: 'dashboard', t: 'Tableau de bord',
    p: ["L'écran d'accueil de l'application donne une vue d'ensemble immédiate."],
    li: ['<b>Alertes actives</b> signalées lors des visites.', '<b>Dernières visites</b> et statistiques du rucher.', '<b>Stocks bas</b> (matériel sous le seuil).', 'Accès rapide au <b>Mode Live</b> de chaque rucher.'],
    img: 'dashboard.jpg',
  },
  {
    id: 'ruchers', t: 'Ruchers',
    p: ['La liste de vos ruchers. Chaque carte ouvre le détail ; le bouton <b>Mode Live</b> lance une visite terrain.'],
    li: ['Créer / modifier / supprimer un rucher (selon droits).', 'Adresse et géolocalisation.'],
    img: 'ruchers.jpg',
  },
  {
    id: 'detail', t: 'Détail d\'un rucher & plan des ruches',
    p: ['Le détail d\'un rucher affiche le <b>plan visuel</b> des ruches, que l\'on peut <b>déplacer par glisser-déposer</b> pour reproduire l\'implantation réelle.'],
    li: ['Ajouter une ruche (numéro NAPI, nom, propriété associative/privée).', 'Ajouter une <b>photo</b> de ruche.', 'Voir la dernière visite et l\'état sanitaire de chaque ruche.'],
    img: 'rucher-detail.jpg',
  },
  {
    id: 'live', t: 'Mode Live (visite terrain)',
    p: ['Interface simplifiée, pensée pour le terrain avec des <b>gants</b> : gros boutons, curseurs, enchaînement automatique des ruches.'],
    li: ['<b>Reine</b> vue ou non, <b>couvain</b> et <b>réserves</b> (0-9), <b>hausses</b>, <b>nourrissement</b>.', '<b>Dictée vocale</b> pour les commentaires.', 'Bouton <b>Alerte</b> pour signaler un problème.', '<b>Mode hors-ligne</b> : saisie sans réseau, synchronisation automatique au retour.'],
    img: 'visite-live.jpg',
  },
  {
    id: 'inventaire', t: 'Inventaire',
    p: ['Gestion du matériel : entrées et sorties, seuils d\'alerte de stock, lien avec la trésorerie.'],
    img: 'inventaire.jpg',
  },
  {
    id: 'tresorerie', t: 'Trésorerie',
    p: ['Recettes et dépenses catégorisées, dépôt de <b>factures</b>, bilan annuel. Réservé aux rôles trésorier/administrateur.'],
    img: 'tresorerie.jpg',
  },
  {
    id: 'miellee', t: 'Miellée',
    p: ['Suivi des récoltes de miel, des pots (stock) et des ventes, avec statistiques.'],
    img: 'miellee.jpg',
  },
  {
    id: 'sanitaire', t: 'Sanitaire',
    p: ['Suivi des traitements (varroa…), comptages et calendrier sanitaire par ruche.'],
    img: 'sanitaire.jpg',
  },
  {
    id: 'meteo', t: 'Météo',
    p: ['Météo locale (Bois-d\'Arcy) : température, hygrométrie, probabilité de pluie et vent, plus le <b>créneau optimal de visite</b> calculé automatiquement (journée douce, sèche, peu ventée).'],
    img: 'meteo.jpg',
  },
  {
    id: 'utilisateurs', t: 'Utilisateurs (admin)',
    p: ['Gestion des comptes : création, modification, <b>suppression</b>, réinitialisation de mot de passe, import CSV, attribution des rôles.'],
    li: ['Rôles : administrateur, responsable de rucher, trésorier, usager, lecture seule.'],
    img: 'utilisateurs.jpg',
  },
  {
    id: 'journal', t: 'Journal (admin)',
    p: ['Historique complet des actions (audit) : qui a fait quoi et quand.'],
    img: 'journal.jpg',
  },
  {
    id: 'installation', t: 'Installer l\'app & travailler hors-ligne',
    p: ['Rucher Manager est une <b>application installable</b> (PWA).'],
    li: ['<b>Android / Chrome</b> : bouton « Installer l\'app ».', '<b>iPhone / Safari</b> : Partager → « Sur l\'écran d\'accueil ».', 'Une fois installée, elle s\'ouvre en plein écran et fonctionne <b>hors-ligne</b> pour la saisie des visites.'],
  },
]

const toc = computed(() => sections.map((s) => ({ id: s.id, t: s.t })))
</script>
