<template>
  <DocArticle
    eyebrow="Prise en main"
    title="Mémo rapide — utilisateur"
    lead="L'essentiel pour saisir vos visites et suivre vos ruches. À garder sous la main."
  >
    <v-alert type="success" variant="tonal" density="comfortable" class="mb-6">
      <b>En bref :</b> ouvrez l'app → bouton <b>Visite rapide</b> (ou <b>Ruchers</b>
      → <b>Mode Live</b>) → pour chaque ruche, réglez les curseurs et validez. C'est tout.
    </v-alert>

    <v-alert type="info" variant="tonal" density="comfortable" class="mb-6">
      <b>Astuce :</b> le bouton <b>« Visite rapide de mes ruches »</b> (tableau de bord
      et onglet <b>Visite</b> du menu mobile) ne fait défiler que <b>vos</b> ruches.
    </v-alert>

    <h2>1. Saisir une visite (mode terrain)</h2>
    <v-timeline side="end" density="compact" class="my-2">
      <v-timeline-item v-for="(s, i) in steps" :key="i" dot-color="primary" size="small">
        <div class="font-weight-bold">{{ s.t }}</div>
        <div class="text-body-2 text-medium-emphasis">{{ s.d }}</div>
      </v-timeline-item>
    </v-timeline>

    <h2>2. Ce qu'on note à chaque visite</h2>
    <v-row>
      <v-col cols="12" sm="6" v-for="c in checks" :key="c.t">
        <div class="d-flex align-start ga-2 mb-1">
          <v-icon color="amber-darken-2">{{ c.i }}</v-icon>
          <div>
            <div class="font-weight-bold">{{ c.t }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ c.d }}</div>
          </div>
        </div>
      </v-col>
    </v-row>

    <h2>3. Déclencher une alerte</h2>
    <p>
      Un problème (reine absente, maladie, colonie faible, agressivité…) ?
      Activez le bouton <b>« ALERTE »</b> pendant la visite et décrivez-le dans le
      commentaire. L'alerte remonte sur le <b>tableau de bord</b> et dans la
      cloche 🔔 en haut de l'écran.
    </p>

    <h2>4. Suivre ses ruches</h2>
    <ul>
      <li><b>Tableau de bord</b> : alertes en cours, dernières visites, stocks bas.</li>
      <li><b>Ruchers</b> → une ruche : historique de ses visites et de son état.</li>
      <li><b>Météo</b> : le <b>créneau optimal</b> pour votre prochaine visite.</li>
    </ul>

    <h2>5. Sans réseau, ça marche quand même</h2>
    <v-alert type="info" variant="tonal" density="comfortable">
      En zone sans réseau, saisissez normalement : les visites sont
      <b>enregistrées sur le téléphone</b> et <b>synchronisées automatiquement</b>
      dès que la connexion revient (badge 🔄 en haut). Pensez à
      <b>installer l'app</b> (« Ajouter à l'écran d'accueil ») pour l'usage terrain.
    </v-alert>

    <div class="mt-6">
      <v-btn color="primary" variant="flat" class="text-none" :to="{ name: 'docs-guide' }" prepend-icon="mdi-book-open-page-variant">
        Voir le guide complet illustré
      </v-btn>
    </div>
  </DocArticle>
</template>

<script setup>
import DocArticle from '../../components/DocArticle.vue'

const steps = [
  { t: 'Ouvrez « Ruchers »', d: 'Choisissez le rucher à visiter.' },
  { t: 'Appuyez sur « Mode Live »', d: 'Interface géante, utilisable avec des gants.' },
  { t: 'Pour chaque ruche', d: 'Reine vue ? Couvain et réserves (curseurs 0-9), hausses, nourrissement.' },
  { t: 'Validez « Suivante »', d: "L'app passe automatiquement à la ruche d'après." },
  { t: 'Terminez', d: 'À la dernière ruche, « Terminer » clôt la visite.' },
]
const checks = [
  { i: 'mdi-crown', t: 'Reine', d: 'Vue ou non (bouton vert / rouge).' },
  { i: 'mdi-grid', t: 'Couvain', d: 'Note de 0 à 9 (corps ouvert).' },
  { i: 'mdi-food-apple', t: 'Réserves', d: 'Miel/pollen, note de 0 à 9.' },
  { i: 'mdi-beehive-outline', t: 'Hausses', d: 'Nombre de hausses posées.' },
  { i: 'mdi-cup-water', t: 'Nourrissement', d: 'Sirop, candi… si donné.' },
  { i: 'mdi-comment-text', t: 'Commentaire', d: 'Dictée vocale possible.' },
]
</script>
