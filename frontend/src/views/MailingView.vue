<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Courriels aux adhérents</h2>
    </div>

    <v-tabs v-model="onglet" color="primary" class="mb-4">
      <v-tab value="ecrire" prepend-icon="mdi-email-edit-outline">Écrire</v-tab>
      <v-tab value="campagnes" prepend-icon="mdi-chart-timeline-variant">
        Campagnes
        <v-badge v-if="campagnes.length" :content="campagnes.length" color="secondary" inline />
      </v-tab>
    </v-tabs>

    <!-- ── Rédaction ────────────────────────────────────────────── -->
    <v-card v-if="onglet === 'ecrire'" variant="outlined">
      <v-card-text>
        <v-select
          v-model="form.audience"
          :items="publics" item-title="libelle" item-value="key"
          label="Destinataires"
          prepend-inner-icon="mdi-account-group"
          :hint="hintPublic" persistent-hint
          class="mb-4"
        />

        <v-text-field
          v-model="form.subject"
          label="Objet"
          prepend-inner-icon="mdi-format-title"
          counter="200" maxlength="200"
          :error-messages="erreurs.subject"
          class="mb-2"
        />

        <RichTextEditor
          ref="editeur"
          v-model="form.body_html"
          label="Message"
          hint="Gras, italique, listes, liens : la mise en forme part avec le message."
          :error="erreurs.body"
          class="mb-4"
        />

        <v-file-input
          v-model="fichiers"
          label="Pièces jointes"
          prepend-icon="mdi-paperclip"
          multiple chips show-size
          :hint="hintPieces" persistent-hint
          class="mb-2"
        />

        <v-checkbox
          v-model="form.tracking"
          color="primary"
          density="compact"
          hide-details
          label="Suivre les ouvertures"
        />
        <!-- Ne pas laisser croire à une mesure exacte : la plupart des
             messageries bloquent les images, d'autres les préchargent. -->
        <p class="text-caption r-muted mb-4 ml-8">
          Deux mécanismes : une image invisible d'un pixel, et les liens du
          message qui passent par une redirection. Beaucoup de messageries
          bloquent les images — le pixel donne donc un <b>minimum</b> — mais un
          <b>clic ne se perd pas</b> et vaut ouverture certaine.
        </p>

        <v-alert v-if="erreur" type="error" density="compact" class="mb-3" closable
                 @click:close="erreur = ''">{{ erreur }}</v-alert>

        <v-alert v-if="bilan" type="success" density="compact" class="mb-3" closable
                 @click:close="bilan = null">
          <b>{{ bilan.sent_count }}</b> message(s) envoyé(s)
          <span v-if="bilan.failed_count">, {{ bilan.failed_count }} en échec</span>.
          <a href="#" class="ml-1" @click.prevent="ouvrir(bilan.id)">Voir le suivi</a>
        </v-alert>
      </v-card-text>
      <v-card-actions class="px-4 pb-4 flex-wrap ga-2">
        <v-btn
          color="primary" prepend-icon="mdi-send" :loading="envoi"
          :disabled="!pret" @click="demanderEnvoi"
        >
          Envoyer à {{ effectif }} adhérent{{ effectif > 1 ? 's' : '' }}
        </v-btn>
        <v-btn
          variant="outlined" prepend-icon="mdi-eye-outline"
          :disabled="!corpsRempli" :loading="apercuEnCours" @click="previsualiser"
        >
          Prévisualiser
        </v-btn>
        <v-btn
          variant="outlined" prepend-icon="mdi-email-fast-outline"
          :disabled="!corpsRempli || !form.subject.trim()" :loading="essai"
          @click="envoyerEssai"
        >
          M'envoyer un essai
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- ── Campagnes ────────────────────────────────────────────── -->
    <template v-if="onglet === 'campagnes'">
      <v-card v-if="!campagnes.length" variant="tonal" class="text-center pa-8">
        <v-icon size="56" color="primary" class="mb-3">mdi-email-outline</v-icon>
        <p class="mb-0 text-medium-emphasis">Aucun message envoyé pour le moment.</p>
      </v-card>

      <v-card v-for="c in campagnes" :key="c.id" variant="outlined" class="mb-3">
        <v-card-item>
          <v-card-title class="text-subtitle-1 d-flex flex-wrap align-center ga-2">
            {{ c.subject }}
            <v-chip size="x-small" variant="tonal">{{ c.audience_label }}</v-chip>
            <v-chip v-if="c.attachments_count" size="x-small" variant="tonal"
                    prepend-icon="mdi-paperclip">{{ c.attachments_count }}</v-chip>
          </v-card-title>
          <v-card-subtitle>
            {{ dateHeure(c.sent_at) }}<span v-if="c.author_name"> — {{ c.author_name }}</span>
          </v-card-subtitle>
        </v-card-item>
        <v-card-text class="pt-0">
          <div class="d-flex flex-wrap align-center ga-2">
            <v-chip size="small" color="success" variant="tonal" prepend-icon="mdi-send-check">
              {{ c.sent_count }} envoyé(s)
            </v-chip>
            <v-chip v-if="c.failed_count" size="small" color="error" variant="tonal"
                    prepend-icon="mdi-alert">{{ c.failed_count }} en échec</v-chip>
            <v-chip v-if="c.tracking" size="small" color="primary" variant="tonal"
                    prepend-icon="mdi-eye-outline">
              {{ c.opened_count }} ouverture(s) — {{ tauxOuverture(c) }}
            </v-chip>
            <v-chip v-if="c.tracking && c.clicked_count" size="small" color="secondary"
                    variant="tonal" prepend-icon="mdi-cursor-default-click-outline">
              {{ c.clicked_count }} clic(s)
            </v-chip>
            <v-chip v-else size="small" variant="tonal" prepend-icon="mdi-eye-off-outline">
              Sans suivi
            </v-chip>
            <v-spacer />
            <v-btn size="small" variant="text" @click="ouvrir(c.id)">Détail</v-btn>
          </div>
        </v-card-text>
      </v-card>
    </template>

    <!-- ── Aperçu ───────────────────────────────────────────────── -->
    <v-dialog v-model="showApercu" max-width="720" scrollable>
      <v-card v-if="apercu">
        <v-card-title class="text-subtitle-1">
          Aperçu — {{ apercu.subject || '(sans objet)' }}
        </v-card-title>
        <v-card-subtitle class="pb-2">
          Rendu exact du message qui sera envoyé.
        </v-card-subtitle>
        <v-divider />
        <v-card-text style="background:#fff">
          <!-- Le HTML vient du serveur, qui l'a désinfecté avec la même liste
               blanche que pour l'envoi : c'est bien ce message-là qui partira. -->
          <div v-html="apercu.html" />
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showApercu = false">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Détail d'une campagne ────────────────────────────────── -->
    <v-dialog v-model="showDetail" max-width="720" scrollable>
      <v-card v-if="detail">
        <v-card-title class="d-flex align-center flex-wrap ga-2">
          {{ detail.subject }}
          <v-chip size="x-small" variant="tonal">{{ detail.audience_label }}</v-chip>
          <v-spacer />
          <v-btn icon size="small" variant="text" @click="showDetail = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <p class="text-caption r-muted">
            Envoyé le {{ dateHeure(detail.sent_at) }}
            <span v-if="detail.author_name">par {{ detail.author_name }}</span>
          </p>

          <v-alert v-if="detail.tracking" type="info" variant="tonal" density="compact" class="mb-3">
            <b>{{ detail.opened_count }}</b> ouverture(s) sur
            <b>{{ detail.sent_count }}</b> envoi(s) — {{ tauxOuverture(detail) }},
            dont <b>{{ detail.clicked_count }}</b> confirmée(s) par un clic.
            Un message lu sans charger les images et sans cliquer n'est pas
            compté : le chiffre réel est au moins celui-ci.
          </v-alert>

          <div v-if="detail.attachments?.length" class="mb-3">
            <v-chip v-for="a in detail.attachments" :key="a.id" size="small"
                    variant="tonal" class="mr-1 mb-1"
                    :prepend-icon="a.hosted ? 'mdi-cloud-download-outline' : 'mdi-paperclip'"
                    :color="a.hosted ? 'secondary' : undefined"
                    link @click="telecharger(a)">
              {{ a.filename }} ({{ taille(a.size) }})
              <span v-if="a.hosted" class="ml-1">
                — déposé, {{ a.download_count }} téléchargement(s)
              </span>
            </v-chip>
            <p v-if="detail.attachments.some((a) => a.hosted)" class="text-caption r-muted mt-1 mb-0">
              Les fichiers déposés ne voyagent pas dans le message : les
              adhérents les récupèrent par un lien, valable jusqu'au
              {{ dateCourte(detail.attachments.find((a) => a.hosted).expires_at) }}.
            </p>
          </div>

          <v-card variant="tonal" class="pa-3 mb-4">
            <!-- Le HTML a été désinfecté par le serveur au moment de l'envoi ;
                 on montre ici exactement ce qui est parti. -->
            <div v-if="detail.body_html" class="text-body-2 r-corps" v-html="detail.body_html" />
            <div v-else class="text-body-2" style="white-space:pre-wrap">{{ detail.body }}</div>
          </v-card>

          <v-table density="compact">
            <thead>
              <tr>
                <th>Adhérent</th>
                <th>Adresse</th>
                <th class="text-center">Envoi</th>
                <th class="text-center">Ouverture</th>
                <th class="text-center">Clic</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in detail.recipients" :key="r.id">
                <td>{{ r.name }}</td>
                <td class="text-caption">{{ r.email }}</td>
                <td class="text-center">
                  <v-icon v-if="r.sent" color="success" size="18">mdi-check</v-icon>
                  <v-tooltip v-else :text="r.error || 'échec'">
                    <template v-slot:activator="{ props }">
                      <v-icon v-bind="props" color="error" size="18">mdi-close</v-icon>
                    </template>
                  </v-tooltip>
                </td>
                <td class="text-center text-caption">
                  <template v-if="r.first_opened_at">
                    {{ dateHeure(r.first_opened_at) }}
                    <span v-if="r.open_count > 1"> ({{ r.open_count }}×)</span>
                  </template>
                  <span v-else class="r-muted">—</span>
                </td>
                <td class="text-center text-caption">
                  <template v-if="r.first_clicked_at">
                    <v-icon color="secondary" size="16">mdi-cursor-default-click-outline</v-icon>
                    <span v-if="r.click_count > 1"> {{ r.click_count }}×</span>
                  </template>
                  <span v-else class="r-muted">—</span>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { toastError, toastSuccess, apiError } from '../services/toast'
import { confirmAction } from '../services/confirm'
import RichTextEditor from '../components/RichTextEditor.vue'

const onglet = ref('ecrire')
const publics = ref([])
const campagnes = ref([])
const fichiers = ref([])
const envoi = ref(false)
const erreur = ref('')
const bilan = ref(null)
const showDetail = ref(false)
const detail = ref(null)
const showApercu = ref(false)
const apercu = ref(null)
const apercuEnCours = ref(false)
const essai = ref(false)
const editeur = ref(null)

// Doit rester aligné sur SEUIL_PIECE_JOINTE côté serveur : c'est lui qui
// tranche, l'interface ne fait qu'annoncer à l'avance ce qu'il décidera.
const SEUIL_HEBERGE = 5 * 1024 * 1024

const form = ref({ audience: 'all', subject: '', body_html: '', tracking: true })
const erreurs = ref({ subject: '', body: '' })

const publicCourant = computed(() =>
  publics.value.find((p) => p.key === form.value.audience))
const effectif = computed(() => publicCourant.value?.count ?? 0)
// Un corps réduit à « <br> » ou « <p></p> » est vide pour le lecteur : on
// juge sur le texte, pas sur la présence de balises.
const corpsRempli = computed(() =>
  form.value.body_html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim().length > 0)
const pret = computed(() =>
  !!form.value.subject.trim() && corpsRempli.value && effectif.value > 0)

const hintPublic = computed(() => {
  if (!publicCourant.value) return ''
  const n = publicCourant.value.count
  return n
    ? `${n} adhérent(s) avec une adresse e-mail renseignée.`
    : "Personne n'est joignable : aucune adresse e-mail renseignée dans ce groupe."
})

const hintPieces = computed(() => {
  const liste = fichiers.value || []
  const lourds = liste.filter((f) => (f.size || 0) > SEUIL_HEBERGE)
  const total = liste.reduce((s, f) => s + (f.size || 0), 0)
  const base = "Au-delà de 5 Mo, le fichier n'est pas joint : il est déposé sur "
    + "l'application et le message porte un lien (valable 90 jours). 50 Mo maximum."
  if (!total) return base
  const quoi = lourds.length
    ? ` — dont ${lourds.length} déposé(s) sur l'application : ${lourds.map((f) => f.name).join(', ')}.`
    : ' — tous joints au message.'
  return `${taille(total)} au total${quoi} ${base}`
})

// Le dossier des pièces jointes n'est pas servi par le serveur web : on passe
// par l'API, qui vérifie le rôle, et on déclenche l'enregistrement nous-mêmes.
async function telecharger(a) {
  try {
    const { data } = await api.get(
      `/mail/campaigns/${detail.value.id}/attachments/${a.id}`,
      { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const lien = document.createElement('a')
    lien.href = url
    lien.download = a.filename
    lien.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    // En « responseType: blob », le corps d'erreur est lui aussi un blob :
    // sans le relire, on perdrait la phrase envoyée par le serveur.
    try {
      if (e?.response?.data instanceof Blob) {
        e.response.data = JSON.parse(await e.response.data.text())
      }
    } catch { /* corps illisible : le message générique fera l'affaire */ }
    toastError(apiError(e, 'Téléchargement impossible'))
  }
}

function taille(o) {
  if (!o) return '0 o'
  if (o < 1024) return o + ' o'
  if (o < 1024 * 1024) return Math.round(o / 1024) + ' Ko'
  return (o / 1024 / 1024).toFixed(1) + ' Mo'
}

function dateCourte(d) {
  return d ? new Date(d).toLocaleDateString('fr-FR') : ''
}

function dateHeure(d) {
  if (!d) return ''
  const x = new Date(d)
  return x.toLocaleDateString('fr-FR')
    + ' à ' + x.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function tauxOuverture(c) {
  if (!c.sent_count) return '—'
  return Math.round((c.opened_count / c.sent_count) * 100) + ' %'
}

async function charger() {
  try {
    const [p, c] = await Promise.all([
      api.get('/mail/audiences'),
      api.get('/mail/campaigns'),
    ])
    publics.value = p.data.map((x) => ({ ...x, libelle: `${x.label} (${x.count})` }))
    campagnes.value = c.data
  } catch (e) { toastError(apiError(e, 'Chargement impossible')) }
}

async function demanderEnvoi() {
  erreurs.value = { subject: '', body: '' }
  erreur.value = ''
  // Un envoi à tous ne se rattrape pas : on fait confirmer, en rappelant
  // combien de personnes vont recevoir le message.
  const quoi = publicCourant.value?.label || 'les adhérents'
  // Sans ces options, le bouton de confirmation dirait « Supprimer » : le
  // libellé par défaut vise la suppression, qui est l'usage le plus courant.
  if (!(await confirmAction(
    `Envoyer « ${form.value.subject.trim()} » à ${effectif.value} adhérent(s) — ${quoi} ? `
    + "Un message parti ne peut pas être rappelé.",
    { title: 'Envoyer le message', confirmText: 'Envoyer', color: 'primary' }
  ))) return

  envoi.value = true
  try {
    const fd = new FormData()
    fd.append('subject', form.value.subject.trim())
    fd.append('body', '')
    fd.append('body_html', form.value.body_html)
    fd.append('audience', form.value.audience)
    fd.append('tracking', form.value.tracking ? 'true' : 'false')
    for (const f of fichiers.value || []) fd.append('files', f)
    const { data } = await api.post('/mail/campaigns', fd,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    bilan.value = data
    form.value = { audience: form.value.audience, subject: '', body_html: '', tracking: true }
    editeur.value?.vider()
    fichiers.value = []
    await charger()
    toastSuccess(`${data.sent_count} message(s) envoyé(s)`)
  } catch (e) {
    erreur.value = apiError(e, "Le message n'a pas pu être envoyé")
  } finally {
    envoi.value = false
  }
}

async function previsualiser() {
  apercuEnCours.value = true
  try {
    const fd = new FormData()
    fd.append('subject', form.value.subject.trim())
    fd.append('body', '')
    fd.append('body_html', form.value.body_html)
    const { data } = await api.post('/mail/preview', fd,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    apercu.value = data
    showApercu.value = true
  } catch (e) {
    toastError(apiError(e, 'Aperçu impossible'))
  } finally {
    apercuEnCours.value = false
  }
}

async function envoyerEssai() {
  essai.value = true
  erreur.value = ''
  try {
    const fd = new FormData()
    fd.append('subject', form.value.subject.trim())
    fd.append('body', '')
    fd.append('body_html', form.value.body_html)
    for (const f of fichiers.value || []) fd.append('files', f)
    const { data } = await api.post('/mail/test', fd,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    toastSuccess(`Essai envoyé à ${data.to}`)
  } catch (e) {
    erreur.value = apiError(e, "L'essai n'a pas pu être envoyé")
  } finally {
    essai.value = false
  }
}

async function ouvrir(id) {
  try {
    const { data } = await api.get(`/mail/campaigns/${id}`)
    detail.value = data
    showDetail.value = true
  } catch (e) { toastError(apiError(e, 'Campagne indisponible')) }
}

onMounted(charger)
</script>

<style scoped>
/* Le corps d'une campagne est du HTML : sans ces règles, listes et citations
   perdraient leur mise en forme dans la fenêtre de détail. */
.r-corps :deep(ul), .r-corps :deep(ol) { padding-left: 22px; margin: 6px 0; }
.r-corps :deep(p) { margin: 0 0 8px; }
.r-corps :deep(blockquote) {
  margin: 8px 0;
  padding-left: 12px;
  border-left: 3px solid rgba(var(--v-border-color), 0.4);
}
</style>
