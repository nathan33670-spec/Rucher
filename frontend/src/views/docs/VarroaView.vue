<template>
  <DocArticle
    eyebrow="Formation apicole"
    title="Le varroa (Varroa destructor)"
    lead="Reconnaître, surveiller et traiter le principal ennemi des colonies d'abeilles."
  >
    <v-alert type="warning" variant="tonal" density="comfortable" class="mb-6">
      Le varroa est aujourd'hui la <b>première cause de mortalité</b> des colonies.
      Une colonie non traitée est très souvent condamnée à moyen terme.
    </v-alert>

    <h2>Qu'est-ce que le varroa ?</h2>
    <p>
      <b>Varroa destructor</b> est un acarien parasite externe de l'abeille, visible
      à l'œil nu (~1,1 mm, brun-roux, ovale). Il se nourrit des réserves de
      l'abeille (corps gras) et transmet de nombreux <b>virus</b>.
    </p>

    <h2>Son cycle : pourquoi il est si redoutable</h2>
    <ul>
      <li>La femelle varroa entre dans une cellule de couvain <b>juste avant l'operculation</b>.</li>
      <li>Elle pond sur la nymphe ; sa descendance se développe et se nourrit à l'abri de l'opercule.</li>
      <li>Il a une <b>nette préférence pour le couvain de mâles</b> (cycle plus long).</li>
      <li>À l'émergence, de nouveaux varroas sortent et repartent parasiter d'autres cellules.</li>
    </ul>
    <p>La population de varroa croît donc en parallèle du couvain, avec un pic dangereux à la fin de l'été.</p>

    <h2>Les dégâts</h2>
    <ul>
      <li>Abeilles affaiblies, à durée de vie réduite.</li>
      <li>Malformations (ailes déformées — virus DWV), naissances avortées.</li>
      <li>Baisse de population, puis <b>effondrement de la colonie</b> (varroose) si rien n'est fait.</li>
    </ul>

    <h2>Surveiller : compter avant de traiter</h2>
    <v-row>
      <v-col cols="12" sm="4" v-for="m in methodes" :key="m.t">
        <v-card variant="outlined" class="h-100">
          <v-card-item>
            <v-icon color="amber-darken-2" size="30">{{ m.i }}</v-icon>
            <v-card-title class="text-subtitle-2 font-weight-bold">{{ m.t }}</v-card-title>
          </v-card-item>
          <v-card-text class="pt-0 text-body-2">{{ m.d }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <p class="mt-3">
      Un comptage régulier (chute naturelle sur lange, ou test sur échantillon
      d'abeilles) permet de <b>décider et vérifier l'efficacité</b> d'un traitement.
      Notez chaque comptage dans l'onglet <b>Sanitaire</b> de l'application.
    </p>

    <h2>Traiter</h2>
    <h3>Méthodes biotechniques (sans médicament)</h3>
    <ul>
      <li>Retrait du <b>couvain de mâles</b> (piégeage).</li>
      <li><b>Encagement de la reine</b> pour créer une rupture de ponte.</li>
      <li>Essaimage / division de colonie.</li>
    </ul>

    <h3>Traitements médicamenteux (avec AMM)</h3>
    <v-table density="comfortable" class="mb-2">
      <thead><tr><th>Substance</th><th>Exemples</th><th>Période typique</th></tr></thead>
      <tbody>
        <tr v-for="t in traitements" :key="t.s"><td class="font-weight-bold">{{ t.s }}</td><td>{{ t.e }}</td><td>{{ t.p }}</td></tr>
      </tbody>
    </v-table>

    <v-alert type="error" variant="tonal" density="comfortable" class="my-4">
      <b>Impératif :</b> n'utilisez que des produits disposant d'une <b>AMM</b>
      (autorisation de mise sur le marché), en respectant strictement doses et
      conditions. Consignez chaque traitement (date, produit, n° de lot, dose)
      dans le <b>registre d'élevage</b> — voir la page Réglementation.
    </v-alert>

    <h2>Stratégie sur l'année</h2>
    <ol>
      <li><b>Traitement principal</b> : juste <b>après la récolte</b> (fin d'été), pour protéger les abeilles d'hiver.</li>
      <li><b>Traitement de finition</b> : en <b>hiver, hors couvain</b> (souvent à l'acide oxalique), très efficace car tous les varroas sont sur les abeilles.</li>
      <li><b>Alterner les molécules</b> pour limiter les résistances (notamment aux amitrazes).</li>
    </ol>

    <div class="mt-6">
      <v-btn color="primary" variant="flat" class="text-none" :to="{ name: 'docs-reglementation' }" prepend-icon="mdi-gavel">
        Obligations & registre des traitements
      </v-btn>
    </div>
  </DocArticle>
</template>

<script setup>
import DocArticle from '../../components/DocArticle.vue'

const methodes = [
  { i: 'mdi-tray-full', t: 'Lange graissé', d: 'Comptage de la chute naturelle de varroas sur plusieurs jours (non invasif).' },
  { i: 'mdi-shaker-outline', t: 'Sucre glace', d: 'Sur ~300 abeilles : le sucre fait décrocher les varroas, sans tuer les abeilles.' },
  { i: 'mdi-cup', t: 'Lavage (alcool)', d: 'Le plus précis, mais létal pour l\'échantillon d\'abeilles prélevé.' },
]
const traitements = [
  { s: 'Amitraze', e: 'Lanières (ex. Apivar)', p: 'Fin d\'été, après récolte (plusieurs semaines)' },
  { s: 'Thymol', e: 'Gels (ex. Apiguard, Apilife Var)', p: 'Fin d\'été (températures douces)' },
  { s: 'Acide formique', e: 'Ex. MAQS, Formic Pro', p: 'Été/fin d\'été (agit dans le couvain)' },
  { s: 'Acide oxalique', e: 'Dégouttement / sublimation', p: 'Hiver, hors couvain (finition)' },
]
</script>
