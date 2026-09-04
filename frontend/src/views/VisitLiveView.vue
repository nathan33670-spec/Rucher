<template>
  <div class="live-mode fill-height">
    <!-- Barre de progression -->
    <v-progress-linear :model-value="progress" color="primary" height="6" class="mb-2" />

    <!-- Indicateur offline -->
    <v-alert v-if="!online" type="warning" density="compact" class="mb-2">
      Mode hors-ligne — les visites seront synchronisées au retour du réseau
    </v-alert>

    <div v-if="currentHive" class="text-center">
      <!-- Qui saisit la visite + accès à l'historique de la ruche -->
      <div class="d-flex align-center ga-2 mb-2 flex-wrap">
        <v-chip size="small" variant="tonal" color="secondary" title="Auteur de la visite">
          <v-icon start size="15">mdi-account-edit</v-icon>
          {{ authorName }}
        </v-chip>
        <v-spacer />
        <v-btn size="small" variant="tonal" color="primary" prepend-icon="mdi-history" @click="showHistory">
          Historique
        </v-btn>
      </div>

      <!-- Sélecteur de ruche -->
      <v-select
        v-model="currentIndex"
        :items="hiveOptions"
        item-title="label"
        item-value="index"
        density="compact"
        variant="outlined"
        class="mb-2"
        hide-details
        style="max-width: 350px; margin: 0 auto;"
      >
        <template v-slot:prepend-inner>
          <v-icon :color="currentHive?.ownership === 'private' ? 'accent' : 'primary'">
            {{ currentHive?.ownership === 'private' ? 'mdi-home' : 'mdi-hexagon' }}
          </v-icon>
        </template>
      </v-select>

      <div class="d-flex align-center justify-center ga-2 mb-4">
        <p class="text-caption r-muted mb-0">{{ currentIndex + 1 }} / {{ hives.length }}</p>
        <v-chip
          :color="currentHive?.ownership === 'private' ? 'accent' : 'info'"
          size="x-small" variant="tonal"
        >
          <v-icon start size="12">{{ currentHive?.ownership === 'private' ? 'mdi-home' : 'mdi-account-group' }}</v-icon>
          {{ currentHive?.ownership === 'private' ? 'Privée' : 'Associative' }}
        </v-chip>
      </div>

      <!-- Provenance des valeurs affichées : sans ce rappel, on ne saurait pas
           distinguer un relevé du jour d'une valeur héritée de la visite
           précédente. -->
      <v-alert
        v-if="prefillFrom"
        density="compact" variant="tonal" color="secondary" class="mb-4 text-left prefill-note"
      >
        <div class="d-flex align-center ga-2 flex-wrap">
          <v-icon size="16">mdi-history</v-icon>
          <span class="text-caption">
            Valeurs reprises de la visite du <b>{{ formatVisitDate(prefillFrom.visited_at) }}</b>
            <template v-if="prefillFrom.author_name"> par {{ prefillFrom.author_name }}</template>.
            Corrigez ce qui a changé.
          </span>
          <v-spacer />
          <v-btn size="x-small" variant="text" density="comfortable" @click="clearPrefill">
            Repartir de zéro
          </v-btn>
        </div>
      </v-alert>
      <v-alert
        v-else-if="currentHive && !lastVisits[currentHive.id]"
        density="compact" variant="tonal" color="info" class="mb-4 text-left"
      >
        <span class="text-caption">
          <v-icon size="15">mdi-information-outline</v-icon>
          Première visite enregistrée pour cette ruche.
        </span>
      </v-alert>

      <!-- ═══ SECTION HAUSSES ═══ -->
      <v-card variant="outlined" class="mb-4 pa-3">
        <div class="text-subtitle-2 font-weight-bold mb-3">
          <v-icon class="mr-1" color="primary">mdi-beehive-outline</v-icon> Hausses
        </div>

        <!-- HAUSSES — nombre avec +/- -->
        <div class="mb-3">
          <p class="text-overline">Nombre de hausses : {{ form.supers_count }}</p>
          <div class="d-flex align-center justify-center ga-3">
            <v-btn icon color="error" size="x-large" min-height="56" min-width="56"
              @click="form.supers_count = Math.max(0, form.supers_count - 1)" :disabled="form.supers_count <= 0">
              <v-icon size="32">mdi-minus-thick</v-icon>
            </v-btn>
            <div class="text-h3 font-weight-bold mx-4" style="min-width:60px;">{{ form.supers_count }}</div>
            <v-btn icon color="success" size="x-large" min-height="56" min-width="56"
              @click="form.supers_count++">
              <v-icon size="32">mdi-plus-thick</v-icon>
            </v-btn>
          </div>
        </div>
      </v-card>

      <!-- ═══ SECTION CORPS ═══ -->
      <v-card variant="outlined" class="mb-4 pa-3">
        <div class="text-subtitle-2 font-weight-bold mb-3">
          <v-icon class="mr-1" color="secondary">mdi-hexagon-multiple</v-icon> Corps
        </div>

        <!-- Corps ouvert ? -->
        <div class="mb-3">
          <v-switch
            v-model="bodyOpened"
            label="Corps ouvert"
            color="primary"
            hide-details
            density="compact"
            class="d-inline-flex"
          />
        </div>

        <!-- CADRES DE CORPS — même compteur que les hausses -->
        <div class="mb-3">
          <p class="text-overline">Cadres de corps : {{ form.frames_count }}</p>
          <div class="d-flex align-center justify-center ga-3">
            <v-btn icon color="error" size="x-large" min-height="56" min-width="56"
              aria-label="Retirer un cadre de corps"
              @click="form.frames_count = Math.max(0, form.frames_count - 1)" :disabled="form.frames_count <= 0">
              <v-icon size="32">mdi-minus-thick</v-icon>
            </v-btn>
            <div class="text-h3 font-weight-bold mx-4" style="min-width:60px;">{{ form.frames_count }}</div>
            <v-btn icon color="success" size="x-large" min-height="56" min-width="56"
              aria-label="Ajouter un cadre de corps"
              @click="form.frames_count++">
              <v-icon size="32">mdi-plus-thick</v-icon>
            </v-btn>
          </div>
        </div>

        <!-- REINE — gros toggle -->
        <div class="mb-3">
          <p class="text-overline">Reine</p>
          <!-- Libellés explicites : une icône seule ne dit pas si l'on
               déclare « reine vue » ou « reine absente ». -->
          <v-btn-toggle v-model="form.queen_seen" mandatory divided variant="outlined" class="d-flex">
            <v-btn :value="true" color="success" size="x-large" class="flex-grow-1" min-height="60">
              <v-icon size="24" class="mr-2">mdi-check-bold</v-icon> Vue
            </v-btn>
            <v-btn :value="false" color="error" size="x-large" class="flex-grow-1" min-height="60">
              <v-icon size="24" class="mr-2">mdi-close-thick</v-icon> Non vue
            </v-btn>
          </v-btn-toggle>
        </div>

        <!-- COUVAIN — gros slider ou N/A -->
        <div class="mb-3">
          <p class="text-overline">Couvain : {{ bodyOpened ? form.brood_score : 'N/A' }}</p>
          <v-slider
            v-if="bodyOpened"
            v-model="form.brood_score"
            :min="0" :max="9" :step="1"
            thumb-label="always"
            color="primary" track-color="primary" thumb-size="40"
          />
          <v-chip v-else color="secondary" variant="tonal" size="large" class="px-6">N/A — corps non ouvert</v-chip>
        </div>

        <!-- RÉSERVES — gros slider ou N/A -->
        <div class="mb-3">
          <p class="text-overline">Réserves : {{ bodyOpened ? form.reserves_score : 'N/A' }}</p>
          <v-slider
            v-if="bodyOpened"
            v-model="form.reserves_score"
            :min="0" :max="9" :step="1"
            thumb-label="always"
            color="accent" track-color="accent" thumb-size="40"
          />
          <v-chip v-else color="secondary" variant="tonal" size="large" class="px-6">N/A — corps non ouvert</v-chip>
        </div>
      </v-card>

      <!-- NOURRISSEMENT rapide -->
      <div class="mb-4">
        <p class="text-overline">Nourrissement</p>
        <v-btn-toggle v-model="form.feeding" class="d-flex flex-wrap">
          <v-btn v-for="opt in feedingOptions" :key="opt" :value="opt" size="large" class="flex-grow-1 ma-1">
            {{ opt }}
          </v-btn>
        </v-btn-toggle>
      </div>

      <!-- ALERTE -->
      <v-btn
        :color="form.is_alert ? 'error' : undefined"
        size="x-large" block class="mb-4" min-height="56"
        @click="form.is_alert = !form.is_alert"
      >
        <v-icon class="mr-2">mdi-alert</v-icon>
        {{ form.is_alert ? 'ALERTE ACTIVÉE' : "Pas d'alerte" }}
      </v-btn>

      <!-- COMMENTAIRE (dictée vocale) -->
      <v-textarea v-model="form.comment" label="Commentaire" rows="3" class="mb-2" />

      <!-- Aperçu en direct de ce que le micro comprend : l'utilisateur voit
           immédiatement si la dictée capte bien ce qu'il dit. -->
      <v-slide-y-transition>
        <v-card v-if="isRecording" class="mb-2 pa-3 text-left dictation-live" :elevation="0">
          <div class="d-flex align-center ga-2 mb-1">
            <span class="rec-dot" />
            <span class="text-caption font-weight-bold">Écoute en cours…</span>
            <v-spacer />
            <span class="text-caption r-muted">{{ interimText ? 'reconnaissance' : 'parlez' }}</span>
          </div>
          <p class="text-body-2 mb-0">
            <span v-if="interimText" class="r-muted font-italic">{{ interimText }}</span>
            <span v-else class="r-muted">Dictez votre observation, le texte s'ajoute au commentaire.</span>
          </p>
        </v-card>
      </v-slide-y-transition>

      <v-btn
        v-if="speechAvailable"
        variant="tonal"
        :color="isRecording ? 'error' : 'primary'"
        size="x-large"
        block
        min-height="56"
        @click="toggleDictation"
        class="mb-2"
      >
        <v-icon size="28" class="mr-2">{{ isRecording ? 'mdi-stop-circle' : 'mdi-microphone' }}</v-icon>
        {{ isRecording ? 'Arrêter la dictée' : 'Dictée vocale' }}
      </v-btn>
      <v-alert v-if="speechError" type="warning" density="compact" class="mb-4" closable @click:close="speechError = ''">
        {{ speechError }}
      </v-alert>
      <div v-else class="mb-4" />

      <!-- NAVIGATION -->
      <v-alert v-if="saveError" type="error" density="compact" class="mb-3" closable @click:close="saveError = ''">
        {{ saveError }}
      </v-alert>

      <!-- Le bouton « précédente » reste étroit : sur un écran de 390 px, trois
           boutons de même largeur débordaient et tronquaient « Terminer ». -->
      <div class="d-flex ga-2 nav-row">
        <v-btn variant="tonal" size="x-large" min-height="56" class="nav-back"
          :disabled="currentIndex === 0" @click="prev" title="Ruche précédente">
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
        <v-btn variant="outlined" size="x-large" min-height="56" class="flex-grow-1 nav-skip"
          @click="skipHive" :disabled="currentIndex >= hives.length">
          <v-icon class="mr-1">mdi-skip-next</v-icon> Passer
        </v-btn>
        <v-btn color="primary" size="x-large" min-height="56" class="flex-grow-1 nav-next"
          @click="saveAndNext" :loading="saving">
          <v-icon class="mr-1">mdi-check</v-icon>
          {{ currentIndex === hives.length - 1 ? 'Terminer' : 'Suivante' }}
        </v-btn>
      </div>

      <v-snackbar v-model="savedSnack" color="success" timeout="1500" location="top">
        Visite enregistrée
      </v-snackbar>
    </div>

    <div v-else class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" v-if="loading" />
      <div v-else-if="savedCount === 0">
        <v-icon size="64" color="grey-lighten-1">mdi-beehive-outline</v-icon>
        <h3 class="mt-4">Aucune ruche à visiter</h3>
        <p class="r-muted">
          {{ mine ? "Vous n'êtes propriétaire d'aucune ruche active pour le moment." : 'Aucune ruche active dans ce rucher.' }}
        </p>
        <v-btn color="primary" class="mt-4" @click="$router.push({ name: mine ? 'dashboard' : 'apiaries' })">
          {{ mine ? "Retour à l'accueil" : 'Retour aux ruchers' }}
        </v-btn>
      </div>
      <div v-else>
        <v-icon size="64" color="success">mdi-check-circle</v-icon>
        <h3 class="mt-4">Visite terminée !</h3>
        <p class="r-muted">{{ savedCount }} ruches visitées</p>
        <v-btn color="primary" class="mt-4" @click="$router.push({ name: mine ? 'dashboard' : 'apiaries' })">
          {{ mine ? "Retour à l'accueil" : 'Retour aux ruchers' }}
        </v-btn>
      </div>
    </div>

    <!-- Historique complet de la ruche sélectionnée -->
    <v-dialog v-model="showHist" max-width="560" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-history</v-icon>
          <span class="text-truncate">Historique — {{ currentHiveLabel }}</span>
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 65vh;">
          <div v-if="loadingHist" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" />
          </div>

          <v-timeline v-else-if="history.length" density="compact" side="end" truncate-line="both">
            <v-timeline-item
              v-for="v in history" :key="v.id"
              :dot-color="v.is_alert ? 'error' : 'primary'"
              :icon="v.is_alert ? 'mdi-alert' : 'mdi-clipboard-check'"
              size="small"
            >
              <div class="d-flex align-center ga-2 flex-wrap">
                <span class="font-weight-bold text-body-2">{{ formatVisitDate(v.visited_at) }}</span>
                <v-chip v-if="v.author_name" size="x-small" variant="tonal" color="secondary">
                  {{ v.author_name }}
                </v-chip>
              </div>

              <!-- Relevés de la visite -->
              <div class="d-flex ga-1 flex-wrap mt-1">
                <v-chip size="x-small" variant="tonal" :color="v.queen_seen ? 'success' : 'error'">
                  <v-icon start size="12">{{ v.queen_seen ? 'mdi-check' : 'mdi-close' }}</v-icon> Reine
                </v-chip>
                <v-chip v-if="v.brood_score != null" size="x-small" variant="tonal">Couvain {{ v.brood_score }}</v-chip>
                <v-chip v-if="v.reserves_score != null" size="x-small" variant="tonal">Réserves {{ v.reserves_score }}</v-chip>
                <v-chip v-if="v.supers_count != null" size="x-small" variant="tonal">{{ v.supers_count }} hausse(s)</v-chip>
                <v-chip v-if="v.frames_count != null" size="x-small" variant="tonal">{{ v.frames_count }} cadre(s)</v-chip>
                <v-chip v-if="v.honey_harvest_kg" size="x-small" variant="tonal" color="primary">{{ v.honey_harvest_kg }} kg miel</v-chip>
                <v-chip v-if="v.pollen_harvest_kg" size="x-small" variant="tonal" color="accent">{{ v.pollen_harvest_kg }} kg pollen</v-chip>
                <v-chip v-if="v.feeding" size="x-small" variant="tonal">{{ v.feeding }}</v-chip>
                <v-chip v-if="v.treatment_type" size="x-small" variant="tonal" color="info">
                  <v-icon start size="12">mdi-medical-bag</v-icon>
                  {{ v.treatment_type }}<template v-if="v.treatment_product"> · {{ v.treatment_product }}</template>
                </v-chip>
              </div>

              <p v-if="v.comment" class="text-body-2 mt-2 mb-0 hist-comment">{{ v.comment }}</p>
            </v-timeline-item>
          </v-timeline>

          <div v-else class="text-center py-8">
            <v-icon size="48" color="grey-lighten-1">mdi-clipboard-text-off-outline</v-icon>
            <p class="r-muted mt-3 mb-0">Aucune visite enregistrée pour cette ruche.</p>
          </div>
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showHist = false">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { apiError } from '../services/toast'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'
import { savePendingVisit, syncPendingVisits } from '../services/offline'
import { useNotifStore } from '../stores/notif'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  apiaryId: [String, Number],
  // « Visite rapide » : ne fait défiler que les ruches dont l'utilisateur
  // courant est propriétaire (gestionnaire), tous ruchers confondus.
  mine: { type: Boolean, default: false },
})
const route = useRoute()
const router = useRouter()
const notif = useNotifStore()
const auth = useAuthStore()

const hives = ref([])
const currentIndex = ref(0)
const loading = ref(true)
const saving = ref(false)
const savedCount = ref(0)
const online = ref(navigator.onLine)
const saveError = ref('')
const savedSnack = ref(false)
const bodyOpened = ref(true)
const isRecording = ref(false)
const interimText = ref('')
const speechError = ref('')
let recognition = null

const feedingOptions = ['Aucun', 'Sirop 50/50', 'Sirop 70/30', 'Candi', 'Pâte protéinée']

// La visite rapide se concentre sur l'observation de la colonie. La récolte se
// saisit dans « Miellée » (elle y devient un lot traçable) et le traitement
// dans le « Suivi sanitaire », qui tient le registre réglementaire.
const EMPTY_FORM = {
  queen_seen: null, brood_score: 5, reserves_score: 5,
  supers_count: 0, frames_count: 0, feeding: 'Aucun', comment: '', is_alert: false,
}

const form = ref({ ...EMPTY_FORM })

// Dernière visite de chaque ruche, chargée en une fois au démarrage de la
// tournée : la saisie repart des valeurs connues, et cela reste disponible
// hors connexion une fois la page ouverte.
const lastVisits = ref({})
// Visite dont proviennent les valeurs affichées (null = saisie repartie de zéro).
const prefillFrom = ref(null)

// Historique de la ruche sélectionnée
const showHist = ref(false)
const loadingHist = ref(false)
const history = ref([])

async function showHistory() {
  if (!currentHive.value) return
  showHist.value = true
  loadingHist.value = true
  history.value = []
  try {
    const { data } = await api.get('/visits/', { params: { hive_id: currentHive.value.id, limit: 50 } })
    history.value = data
  } catch { history.value = [] }
  finally { loadingHist.value = false }
}

function formatVisitDate(iso) {
  return new Date(iso).toLocaleString('fr-FR', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

const currentHive = computed(() => hives.value[currentIndex.value] || null)
const currentHiveLabel = computed(() => {
  const h = currentHive.value
  return h ? (h.name || h.napi_number || 'Ruche #' + h.id) : ''
})
// Nom affiché de la personne qui saisit la visite.
const authorName = computed(() => {
  const u = auth.user
  if (!u) return 'Moi'
  return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email
})
const progress = computed(() => hives.value.length ? ((currentIndex.value) / hives.value.length) * 100 : 0)

const hiveOptions = computed(() =>
  hives.value.map((h, i) => ({
    index: i,
    label: (i + 1) + '. ' + (h.name || h.napi_number || 'Ruche #' + h.id) + (h.ownership === 'private' ? ' · privée' : ''),
  }))
)

const speechAvailable = ref('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)

// ─── Dictée vocale ────────────────────────────────────────────────
// Sur Android/Chrome, la reconnaissance s'arrête d'elle-même après quelques
// secondes de silence : sans relance, la fin de la dictée était perdue (le
// texte ne correspondait pas à ce qui avait été dicté). On relance donc tant
// que l'utilisateur n'a pas explicitement arrêté, et on repart à chaque fois
// du texte déjà validé pour ne rien écraser ni dupliquer.
let wantRecording = false     // intention de l'utilisateur (≠ état du moteur)
let baseText = ''             // commentaire au moment du démarrage de la dictée

function startRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SR()
  recognition.lang = 'fr-FR'
  recognition.continuous = true
  recognition.interimResults = true    // aperçu en direct
  recognition.maxAlternatives = 1

  recognition.onresult = (e) => {
    let finals = ''
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const txt = e.results[i][0].transcript
      if (e.results[i].isFinal) finals += txt
      else interim += txt
    }
    if (finals) {
      baseText = appendSentence(baseText, finals)
      form.value.comment = baseText
    }
    interimText.value = interim.trim()
  }

  recognition.onerror = (e) => {
    // « no-speech » et « aborted » sont normaux : on laisse onend relancer.
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      wantRecording = false
      isRecording.value = false
      speechError.value = "Micro refusé. Autorisez l'accès au microphone dans votre navigateur."
    } else if (e.error === 'audio-capture') {
      wantRecording = false
      isRecording.value = false
      speechError.value = 'Aucun micro détecté sur cet appareil.'
    }
  }

  recognition.onend = () => {
    // Relance tant que l'utilisateur n'a pas appuyé sur « Arrêter ».
    if (wantRecording) {
      try {
        recognition.start()
      } catch {
        // La relance a échoué : on rend la main plutôt que de laisser
        // l'interface bloquée sur « écoute en cours ».
        wantRecording = false
        isRecording.value = false
        interimText.value = ''
      }
    } else {
      isRecording.value = false
      interimText.value = ''
    }
  }

  recognition.start()
}

/** Concatène proprement : espace, et majuscule en début de phrase. */
function appendSentence(base, addition) {
  let txt = addition.trim()
  if (!txt) return base
  const prev = base.trimEnd()
  if (!prev) return txt.charAt(0).toUpperCase() + txt.slice(1)
  // Après un point, on remet une majuscule.
  const needsCap = /[.!?]$/.test(prev)
  if (needsCap) txt = txt.charAt(0).toUpperCase() + txt.slice(1)
  return prev + ' ' + txt
}

function toggleDictation() {
  if (isRecording.value) {
    wantRecording = false
    isRecording.value = false
    interimText.value = ''
    try { recognition?.stop() } catch { /* ignore */ }
    return
  }
  speechError.value = ''
  baseText = form.value.comment || ''
  wantRecording = true
  isRecording.value = true
  try {
    startRecognition()
  } catch {
    wantRecording = false
    isRecording.value = false
    speechError.value = 'La dictée vocale est indisponible sur ce navigateur.'
  }
}

function stopDictation() {
  wantRecording = false
  isRecording.value = false
  interimText.value = ''
  try { recognition?.stop() } catch { /* ignore */ }
}

/**
 * Prépare le formulaire pour la ruche courante.
 *
 * On repart des valeurs de la dernière visite : sur le terrain, le nombre de
 * hausses, de cadres ou le nourrissement changent rarement d'une visite à
 * l'autre. Repartir de zéro obligeait à tout ressaisir et faussait les
 * relevés quand on oubliait un champ.
 *
 * Le commentaire, l'alerte et l'état « corps ouvert » ne sont jamais repris :
 * ils décrivent la visite en cours, pas l'état de la colonie.
 */
function resetForm({ blank = false } = {}) {
  // Changer de ruche coupe la dictée : sans cela le texte dicté partirait
  // dans le commentaire de la ruche suivante.
  stopDictation()
  form.value = { ...EMPTY_FORM }
  bodyOpened.value = true
  prefillFrom.value = null
  if (blank) return

  const last = currentHive.value ? lastVisits.value[currentHive.value.id] : null
  if (!last) return

  const f = form.value
  if (last.queen_seen !== null && last.queen_seen !== undefined) f.queen_seen = last.queen_seen
  if (last.brood_score !== null && last.brood_score !== undefined) f.brood_score = last.brood_score
  if (last.reserves_score !== null && last.reserves_score !== undefined) f.reserves_score = last.reserves_score
  if (last.supers_count !== null && last.supers_count !== undefined) f.supers_count = last.supers_count
  if (last.frames_count !== null && last.frames_count !== undefined) f.frames_count = last.frames_count
  if (last.feeding) f.feeding = last.feeding
  prefillFrom.value = last
}

/** Repartir d'une fiche vierge quand rien de la dernière visite ne s'applique. */
function clearPrefill() {
  resetForm({ blank: true })
}

async function saveAndNext() {
  if (!currentHive.value) return
  saving.value = true
  saveError.value = ''

  const visitData = {
    hive_id: currentHive.value.id,
    visited_at: new Date().toISOString(),
    queen_seen: form.value.queen_seen,
    brood_score: bodyOpened.value ? form.value.brood_score : null,
    reserves_score: bodyOpened.value ? form.value.reserves_score : null,
    supers_count: form.value.supers_count,
    frames_count: form.value.frames_count,
    supers_delta: 0,
    feeding: form.value.feeding === 'Aucun' ? null : form.value.feeding,
    comment: form.value.comment || null,
    is_alert: form.value.is_alert,
    alert_message: form.value.is_alert ? (form.value.comment || 'Alerte terrain') : null,
    is_live_mode: true,
  }

  try {
    if (online.value) {
      await api.post('/visits/', visitData)
      savedSnack.value = true
    } else {
      await savePendingVisit(visitData)
      savedSnack.value = true
    }

    if (form.value.is_alert) {
      notif.addAlert({
        message: form.value.comment || 'Alerte terrain',
        hiveName: currentHive.value.name || ('Ruche #' + currentHive.value.id),
        date: new Date().toLocaleString('fr-FR'),
      })
    }

    savedCount.value++
    rememberAsLast(visitData)
    if (currentIndex.value < hives.value.length - 1) {
      currentIndex.value++
      resetForm()
    } else {
      hives.value = []
    }
  } catch (e) {
    console.error('Save visit error:', e)
    // Le serveur a répondu (saisie refusée, droits manquants…) : le message est
    // affiché tel quel. Sans réponse du tout, on bascule en file d'attente
    // hors-ligne — c'est le cas d'usage terrain, pas une erreur à afficher.
    if (e?.response) {
      saveError.value = apiError(e, "Impossible d'enregistrer la visite")
    } else {
      try {
        await savePendingVisit(visitData)
        savedSnack.value = true
        savedCount.value++
        rememberAsLast(visitData)
        if (currentIndex.value < hives.value.length - 1) {
          currentIndex.value++
          resetForm()
        } else {
          hives.value = []
        }
      } catch (offlineErr) {
        saveError.value = "Impossible d'enregistrer la visite"
      }
    }
  } finally {
    saving.value = false
  }
}

/**
 * La visite qu'on vient de saisir devient la référence de cette ruche : revenir
 * dessus, ou refaire une tournée, repart de ce qui a réellement été relevé —
 * y compris hors connexion, où le serveur ne peut pas nous le confirmer.
 */
function rememberAsLast(visitData) {
  lastVisits.value[visitData.hive_id] = {
    visited_at: visitData.visited_at,
    queen_seen: visitData.queen_seen,
    brood_score: visitData.brood_score,
    reserves_score: visitData.reserves_score,
    supers_count: visitData.supers_count,
    frames_count: visitData.frames_count,
    feeding: visitData.feeding,
    is_alert: visitData.is_alert,
    author_name: authorName.value,
  }
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    resetForm()
  }
}

function skipHive() {
  if (currentIndex.value < hives.value.length - 1) {
    currentIndex.value++
    resetForm()
  } else {
    hives.value = []
  }
}

function onOnline() {
  online.value = true
  syncPendingVisits(api)
}
function onOffline() { online.value = false }

onMounted(async () => {
  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)
  try {
    const url = props.mine
      ? '/apiaries/hives/mine'
      : '/apiaries/' + (props.apiaryId || route.params.apiaryId) + '/hives/editable'
    const { data } = await api.get(url)
    hives.value = data
    if (data.length) {
      // Un seul appel pour toute la tournée : la suite fonctionne même si le
      // réseau tombe une fois sur le rucher.
      try {
        const ids = data.map((h) => h.id).join(',')
        const res = await api.get('/visits/last', { params: { hive_ids: ids } })
        lastVisits.value = res.data || {}
      } catch { lastVisits.value = {} }
      resetForm()
    }
  } catch {}
  loading.value = false
})

onUnmounted(() => {
  window.removeEventListener('online', onOnline)
  window.removeEventListener('offline', onOffline)
  stopDictation()
})
</script>

<style scoped>
.live-mode {
  max-width: 500px;
  margin: 0 auto;
  padding: 16px;
}

/* Bandeau de provenance : présent mais jamais concurrent des champs de saisie. */
.prefill-note {
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* Aperçu de dictée : bandeau discret avec témoin d'enregistrement. */
.dictation-live {
  background: rgba(179, 38, 30, 0.05);
  border-color: rgba(179, 38, 30, 0.28) !important;
}

.rec-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #B3261E;
  animation: rec-pulse 1.4s ease-in-out infinite;
  flex: none;
}

@keyframes rec-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.82); }
}

@media (prefers-reduced-motion: reduce) {
  .rec-dot { animation: none; }
}

/* Barre de navigation entre ruches : jamais de débordement horizontal. */
.nav-row {
  min-width: 0;
}

.nav-back {
  flex: 0 0 auto;
  min-width: 56px !important;
  padding-inline: 0 !important;
}

.nav-skip,
.nav-next {
  min-width: 0 !important;
  padding-inline: 10px !important;
}

/* Sur les écrans étroits, on réduit encore le libellé plutôt que de tronquer. */
@media (max-width: 380px) {
  .nav-skip :deep(.v-btn__content),
  .nav-next :deep(.v-btn__content) {
    font-size: 0.875rem;
  }
}

/* Commentaire d'historique : respecte les retours à la ligne. */
.hist-comment {
  white-space: pre-line;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(93, 64, 55, 0.05);
}
</style>
