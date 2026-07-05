<template>
  <DocArticle
    eyebrow="Formation apicole"
    title="Réglementation & registres (France)"
    lead="Les principales obligations de tout détenteur de ruches, même amateur."
  >
    <v-alert type="warning" variant="tonal" density="comfortable" class="mb-6">
      Cette page est un <b>résumé pédagogique</b> et non un texte officiel. La
      réglementation évolue : vérifiez toujours auprès des sources officielles
      (ministère de l'Agriculture, DDPP/DGAL, GDS, votre syndicat apicole).
    </v-alert>

    <h2>1. Déclarer ses ruches (obligatoire)</h2>
    <ul>
      <li>Tout détenteur de ruches doit <b>déclarer ses colonies chaque année</b>, <b>même pour une seule ruche</b>.</li>
      <li>La déclaration annuelle se fait pendant la <b>période obligatoire, du 1<sup>er</sup> septembre au 31 décembre</b>, via la téléprocédure du ministère de l'Agriculture.</li>
      <li>Une déclaration <b>hors période</b> est possible en cours d'année (par exemple pour un nouvel apiculteur ou pour obtenir un récépissé), mais ne dispense pas de la déclaration annuelle.</li>
      <li>La déclaration attribue / confirme un <b>numéro d'apiculteur (NAPI)</b> et génère un <b>récépissé</b>.</li>
    </ul>
    <v-alert type="info" variant="tonal" density="comfortable" class="mb-4">
      Le NAPI est indispensable pour toute démarche (aides, sanitaire, vente) et
      pour l'<b>identification de vos ruchers</b>.
    </v-alert>

    <h2>2. Identifier ses ruchers</h2>
    <ul>
      <li>Chaque rucher doit porter le <b>numéro NAPI</b> de façon visible : soit sur un <b>panneau</b>, soit inscrit sur au moins <b>une ruche sur dix</b>.</li>
      <li>Les caractères doivent être lisibles (hauteur minimale usuelle : 8 cm).</li>
    </ul>
    <p class="text-body-2 text-medium-emphasis">
      Dans l'application, renseignez le <b>numéro NAPI</b> de chaque ruche pour
      garder la traçabilité (écran « Ruchers → détail »).
    </p>

    <h2>3. Le registre d'élevage (obligatoire)</h2>
    <p>Prévu par la réglementation sanitaire, il doit être tenu à jour et <b>conservé au moins 5 ans</b>. Il comprend en pratique :</p>
    <ul>
      <li>l'<b>identification de l'exploitation</b> (détenteur, NAPI, emplacements) ;</li>
      <li>le suivi des <b>mouvements</b> (achats/ventes/dons de colonies, essaims, cheptel) ;</li>
      <li>l'<b>encadrement sanitaire</b> (intervenants, visites vétérinaires le cas échéant) ;</li>
      <li>le <b>registre des traitements médicamenteux</b>.</li>
    </ul>

    <h3>Registre des traitements</h3>
    <p>Pour chaque traitement (varroa notamment), notez :</p>
    <v-table density="comfortable" class="mb-2">
      <thead><tr><th>À consigner</th><th>Exemple</th></tr></thead>
      <tbody>
        <tr><td class="font-weight-bold">Date</td><td>Date de pose / d'administration</td></tr>
        <tr><td class="font-weight-bold">Produit</td><td>Nom commercial (avec AMM)</td></tr>
        <tr><td class="font-weight-bold">N° de lot</td><td>Numéro figurant sur l'emballage</td></tr>
        <tr><td class="font-weight-bold">Dose / quantité</td><td>Selon la notice</td></tr>
        <tr><td class="font-weight-bold">Ruches concernées</td><td>Identifiants / rucher</td></tr>
        <tr><td class="font-weight-bold">Ordonnance</td><td>À conserver si applicable</td></tr>
      </tbody>
    </v-table>
    <v-alert type="success" variant="tonal" density="comfortable" class="mb-4">
      L'onglet <b>Sanitaire</b> de l'application vous aide à tracer traitements et
      comptages. ⚠️ Il <b>ne remplace pas</b> le registre d'élevage officiel :
      conservez aussi vos ordonnances et documents.
    </v-alert>

    <h2>4. Santé des colonies — dangers sanitaires</h2>
    <ul>
      <li>Certaines maladies (ex. <b>loque américaine</b>) sont des <b>dangers sanitaires réglementés</b> : leur suspicion doit être signalée aux services compétents (DDPP/GDS).</li>
      <li>Le varroa (varroose) fait l'objet d'une lutte obligatoire de fait : il doit être surveillé et traité.</li>
    </ul>

    <h2>5. Vendre son miel</h2>
    <ul>
      <li><b>Étiquetage</b> : dénomination « miel », <b>origine</b> (pays de récolte), <b>poids net</b>, <b>DDM</b> (date de durabilité minimale), coordonnées du producteur, <b>numéro de lot</b>.</li>
      <li><b>Hygiène</b> : respect des règles du « paquet hygiène » (locaux, matériel, traçabilité).</li>
      <li>Selon l'activité, des <b>déclarations</b> complémentaires peuvent être nécessaires.</li>
    </ul>

    <h2>6. Bon voisinage & emplacement</h2>
    <ul>
      <li>Des <b>distances</b> vis-à-vis des voisins et voies publiques peuvent être fixées par <b>arrêté préfectoral/municipal</b> (variables selon les départements).</li>
      <li>Des haies ou palissades (~2 m) devant les entrées peuvent dispenser de distance en obligeant les abeilles à prendre de la hauteur.</li>
    </ul>

    <v-card variant="tonal" color="primary" class="mt-6">
      <v-card-item><v-card-title class="text-subtitle-1 font-weight-bold">Sources officielles à consulter</v-card-title></v-card-item>
      <v-card-text>
        <ul class="mb-0">
          <li>Ministère de l'Agriculture — déclaration de ruches (téléprocédure).</li>
          <li>DGAL / DDPP de votre département — questions sanitaires.</li>
          <li>GDS / GDSA et syndicats apicoles — accompagnement local.</li>
        </ul>
      </v-card-text>
    </v-card>
  </DocArticle>
</template>

<script setup>
import DocArticle from '../../components/DocArticle.vue'
</script>
