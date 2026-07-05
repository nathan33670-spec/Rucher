<template>
  <DocArticle
    eyebrow="Formation apicole"
    title="Le cycle de vie de l'abeille"
    lead="De l'œuf à la butineuse : comprendre le développement et l'organisation de la colonie."
  >
    <h2>Les trois castes</h2>
    <v-row>
      <v-col cols="12" sm="4" v-for="c in castes" :key="c.t">
        <v-card variant="tonal" :color="c.color" class="h-100">
          <v-card-item>
            <div class="text-h4">{{ c.emoji }}</div>
            <v-card-title class="text-subtitle-1 font-weight-bold">{{ c.t }}</v-card-title>
          </v-card-item>
          <v-card-text class="pt-0">{{ c.d }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <h2>Durée de développement (de l'œuf à l'émergence)</h2>
    <v-table density="comfortable" class="mb-2">
      <thead>
        <tr><th>Caste</th><th>Œuf</th><th>Larve</th><th>Operculation → émergence</th><th class="font-weight-bold">Total</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in dev" :key="r.c">
          <td class="font-weight-bold">{{ r.c }}</td><td>{{ r.o }}</td><td>{{ r.l }}</td><td>{{ r.n }}</td>
          <td class="font-weight-bold">{{ r.total }}</td>
        </tr>
      </tbody>
    </v-table>
    <p class="text-caption text-medium-emphasis">
      Les durées varient légèrement selon la température du couvain (~35 °C) et la génétique.
    </p>

    <h2>Les étapes du développement</h2>
    <ol>
      <li><b>Œuf</b> (~3 jours) : pondu par la reine au fond d'une cellule.</li>
      <li><b>Larve</b> : nourrie par les nourrices (gelée royale puis miel/pollen). Elle grandit et remplit la cellule.</li>
      <li><b>Operculation</b> : la cellule est fermée d'un opercule de cire.</li>
      <li><b>Nymphe</b> : métamorphose à l'intérieur de la cellule operculée.</li>
      <li><b>Émergence</b> : la jeune abeille découpe l'opercule et sort.</li>
    </ol>

    <h2>La vie d'une ouvrière : des métiers qui évoluent avec l'âge</h2>
    <v-timeline side="end" density="compact" class="my-2">
      <v-timeline-item v-for="j in jobs" :key="j.t" dot-color="amber-darken-2" size="small">
        <div class="font-weight-bold">{{ j.age }} — {{ j.t }}</div>
        <div class="text-body-2 text-medium-emphasis">{{ j.d }}</div>
      </v-timeline-item>
    </v-timeline>

    <h2>La reine et les mâles</h2>
    <ul>
      <li><b>La reine</b> : seule pondeuse (jusqu'à ~2 000 œufs/jour au printemps). Elle diffuse des phéromones qui assurent la cohésion de la colonie. Espérance de vie : <b>3 à 5 ans</b> (mais remplacée par l'apiculteur souvent avant).</li>
      <li><b>Les mâles (faux-bourdons)</b> : leur unique rôle est de féconder une reine lors du vol nuptial. Ils ne piquent pas, ne butinent pas ; ils sont chassés de la ruche à l'automne.</li>
    </ul>

    <h2>La colonie au fil des saisons</h2>
    <v-row>
      <v-col cols="12" sm="6" v-for="s in saisons" :key="s.t">
        <div class="d-flex align-start ga-2 mb-2">
          <v-icon :color="s.color">{{ s.i }}</v-icon>
          <div>
            <div class="font-weight-bold">{{ s.t }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ s.d }}</div>
          </div>
        </div>
      </v-col>
    </v-row>

    <v-alert type="info" variant="tonal" class="mt-4" density="comfortable">
      <b>Bon à savoir :</b> une ouvrière d'été vit ~5 à 6 semaines (usée par le
      butinage), tandis qu'une ouvrière « d'hiver » vit plusieurs mois et assure
      la survie de la colonie jusqu'au printemps.
    </v-alert>
  </DocArticle>
</template>

<script setup>
import DocArticle from '../../components/DocArticle.vue'

const castes = [
  { emoji: '👑', t: 'La reine', d: "Une seule par colonie. Pond les œufs et régule la ruche par ses phéromones.", color: 'purple' },
  { emoji: '🐝', t: "L'ouvrière", d: 'Femelle stérile. Assure tous les travaux : soins, cire, garde, butinage.', color: 'amber-darken-2' },
  { emoji: '🛩️', t: 'Le mâle', d: 'Faux-bourdon. Féconde les reines ; présent surtout au printemps/été.', color: 'blue-grey' },
]
const dev = [
  { c: 'Reine', o: '3 j', l: '~5,5 j', n: '~7,5 j', total: '~16 jours' },
  { c: 'Ouvrière', o: '3 j', l: '~6 j', n: '~12 j', total: '~21 jours' },
  { c: 'Mâle', o: '3 j', l: '~6,5 j', n: '~14,5 j', total: '~24 jours' },
]
const jobs = [
  { age: 'Jours 1-3', t: 'Nettoyeuse', d: 'Nettoie et prépare les cellules.' },
  { age: 'Jours 3-10', t: 'Nourrice', d: 'Nourrit le couvain (gelée royale, miel, pollen).' },
  { age: 'Jours 10-16', t: 'Cirière / bâtisseuse', d: 'Produit la cire et bâtit les rayons.' },
  { age: 'Jours 16-20', t: 'Manutentionnaire / ventileuse', d: 'Stocke le nectar, ventile, régule température et humidité.' },
  { age: 'Jours 18-21', t: 'Gardienne', d: "Défend l'entrée de la ruche." },
  { age: 'À partir de ~21 j', t: 'Butineuse', d: 'Récolte nectar, pollen, eau et propolis jusqu\'à la fin de sa vie.' },
]
const saisons = [
  { i: 'mdi-snowflake', color: 'blue', t: 'Hiver', d: 'La colonie se met en grappe autour de la reine, consomme ses réserves. Peu ou pas de couvain.' },
  { i: 'mdi-flower', color: 'green', t: 'Printemps', d: 'Reprise de ponte, développement rapide, premières miellées. Risque d\'essaimage.' },
  { i: 'mdi-white-balance-sunny', color: 'amber-darken-2', t: 'Été', d: 'Population maximale, grandes miellées, récoltes. Surveillance du varroa.' },
  { i: 'mdi-leaf-maple', color: 'deep-orange', t: 'Automne', d: 'Élevage des abeilles d\'hiver, traitement varroa, mise en hivernage et nourrissement si besoin.' },
]
</script>
