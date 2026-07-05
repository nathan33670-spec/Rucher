<template>
  <div class="live-mode fill-height">
    <!-- Barre de progression -->
    <v-progress-linear :model-value="progress" color="primary" height="6" class="mb-2" />

    <!-- Indicateur offline -->
    <v-alert v-if="!online" type="warning" density="compact" class="mb-2">
      Mode hors-ligne — les visites seront synchronisées au retour du réseau
    </v-alert>

    <div v-if="currentHive" class="text-center">
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
          <v-icon :color="currentHive?.ownership === 'private' ? 'orange' : 'amber-darken-3'">
            {{ currentHive?.ownership === 'private' ? 'mdi-home' : 'mdi-hexagon' }}
          </v-icon>
        </template>
      </v-select>

      <div class="d-flex align-center justify-center ga-2 mb-4">
        <p class="text-caption text-grey mb-0">{{ currentIndex + 1 }} / {{ hives.length }}</p>
        <v-chip
          :color="currentHive?.ownership === 'private' ? 'orange' : 'blue'"
          size="x-small" variant="tonal"
        >
          {{ currentHive?.ownership === 'private' ? '🏠 Privée' : '🏛️ Associative' }}
        </v-chip>
      </div>

      <!-- ═══ SECTION HAUSSES ═══ -->
      <v-card variant="outlined" class="mb-4 pa-3">
        <div class="text-subtitle-2 font-weight-bold mb-3">
          <v-icon class="mr-1" color="amber-darken-3">mdi-beehive-outline</v-icon> Hausses
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
          <v-icon class="mr-1" color="deep-orange">mdi-hexagon-multiple</v-icon> Corps
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

        <!-- REINE — gros toggle -->
        <div class="mb-3">
          <p class="text-overline">Reine</p>
          <v-btn-toggle v-model="form.queen_seen" mandatory class="d-flex">
            <v-btn :value="true" color="success" size="x-large" class="flex-grow-1" min-height="60">
              <v-icon size="28">mdi-check-bold</v-icon>
            </v-btn>
            <v-btn :value="false" color="error" size="x-large" class="flex-grow-1" min-height="60">
              <v-icon size="28">mdi-close-thick</v-icon>
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
            color="amber" track-color="amber-lighten-3" thumb-size="40"
          />
          <v-chip v-else color="grey" variant="tonal" size="large" class="px-6">N/A — corps non ouvert</v-chip>
        </div>

        <!-- RÉSERVES — gros slider ou N/A -->
        <div class="mb-3">
          <p class="text-overline">Réserves : {{ bodyOpened ? form.reserves_score : 'N/A' }}</p>
          <v-slider
            v-if="bodyOpened"
            v-model="form.reserves_score"
            :min="0" :max="9" :step="1"
            thumb-label="always"
            color="deep-orange" track-color="deep-orange-lighten-3" thumb-size="40"
          />
          <v-chip v-else color="grey" variant="tonal" size="large" class="px-6">N/A — corps non ouvert</v-chip>
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
        :color="form.is_alert ? 'error' : 'grey-lighten-2'"
        size="x-large" block class="mb-4" min-height="56"
        @click="form.is_alert = !form.is_alert"
      >
        <v-icon class="mr-2">mdi-alert</v-icon>
        {{ form.is_alert ? 'ALERTE ACTIVÉE' : "Pas d'alerte" }}
      </v-btn>

      <!-- COMMENTAIRE (dictée vocale) -->
      <v-textarea v-model="form.comment" label="Commentaire" rows="2" class="mb-2" />
      <v-btn
        v-if="speechAvailable"
        variant="tonal"
        :color="isRecording ? 'error' : 'primary'"
        size="x-large"
        block
        min-height="56"
        @click="toggleDictation"
        class="mb-4"
      >
        <v-icon size="28" class="mr-2">{{ isRecording ? 'mdi-microphone-off' : 'mdi-microphone' }}</v-icon>
        {{ isRecording ? 'Arrêter la dictée' : 'Dictée vocale' }}
      </v-btn>

      <!-- NAVIGATION -->
      <v-alert v-if="saveError" type="error" density="compact" class="mb-3" closable @click:close="saveError = ''">
        {{ saveError }}
      </v-alert>

      <div class="d-flex ga-3">
        <v-btn color="grey" size="x-large" class="flex-grow-1" :disabled="currentIndex === 0" @click="prev" min-height="56">
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
        <v-btn color="grey-darken-1" variant="outlined" size="x-large" class="flex-grow-1" @click="skipHive" min-height="56"
          :disabled="currentIndex >= hives.length">
          <v-icon class="mr-1">mdi-skip-next</v-icon> Passer
        </v-btn>
        <v-btn color="primary" size="x-large" class="flex-grow-1" @click="saveAndNext" :loading="saving" min-height="56">
          <v-icon class="mr-1">mdi-check</v-icon>
          {{ currentIndex === hives.length - 1 ? 'Terminer' : 'Suivante' }}
        </v-btn>
      </div>

      <v-snackbar v-model="savedSnack" color="success" timeout="1500" location="top">
        ✅ Visite enregistrée
      </v-snackbar>
    </div>

    <div v-else class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" v-if="loading" />
      <div v-else>
        <v-icon size="64" color="success">mdi-check-circle</v-icon>
        <h3 class="mt-4">Visite terminée !</h3>
        <p class="text-grey">{{ savedCount }} ruches visitées</p>
        <v-btn color="primary" class="mt-4" @click="$router.push('/apiaries')">Retour aux ruchers</v-btn>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'
import { savePendingVisit, syncPendingVisits } from '../services/offline'
import { useNotifStore } from '../stores/notif'

const props = defineProps({ apiaryId: [String, Number] })
const route = useRoute()
const router = useRouter()
const notif = useNotifStore()

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
let recognition = null

const feedingOptions = ['Aucun', 'Sirop 50/50', 'Sirop 70/30', 'Candi', 'Pâte protéinée']

const form = ref({
  queen_seen: null, brood_score: 5, reserves_score: 5,
  supers_count: 0, feeding: 'Aucun', comment: '', is_alert: false, honey_harvest_kg: null,
})

const currentHive = computed(() => hives.value[currentIndex.value] || null)
const progress = computed(() => hives.value.length ? ((currentIndex.value) / hives.value.length) * 100 : 0)

const hiveOptions = computed(() =>
  hives.value.map((h, i) => ({
    index: i,
    label: (i + 1) + '. ' + (h.name || h.napi_number || 'Ruche #' + h.id) + (h.ownership === 'private' ? ' 🏠' : ' 🏛️'),
  }))
)

const speechAvailable = ref('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)

function toggleDictation() {
  if (isRecording.value) {
    recognition?.stop()
    isRecording.value = false
    return
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SR()
  recognition.lang = 'fr-FR'
  recognition.continuous = true
  recognition.interimResults = false
  recognition.onresult = (e) => {
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        form.value.comment += (form.value.comment ? ' ' : '') + e.results[i][0].transcript
      }
    }
  }
  recognition.onend = () => { isRecording.value = false }
  recognition.start()
  isRecording.value = true
}

function resetForm() {
  form.value = {
    queen_seen: null, brood_score: 5, reserves_score: 5,
    supers_count: 0, feeding: 'Aucun', comment: '', is_alert: false, honey_harvest_kg: null,
  }
  bodyOpened.value = true
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
    supers_delta: 0,
    feeding: form.value.feeding === 'Aucun' ? null : form.value.feeding,
    comment: form.value.comment || null,
    is_alert: form.value.is_alert,
    alert_message: form.value.is_alert ? (form.value.comment || 'Alerte terrain') : null,
    honey_harvest_kg: form.value.honey_harvest_kg,
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
    if (currentIndex.value < hives.value.length - 1) {
      currentIndex.value++
      resetForm()
    } else {
      hives.value = []
    }
  } catch (e) {
    console.error('Save visit error:', e)
    const detail = e.response?.data?.detail
    if (detail) {
      saveError.value = 'Erreur : ' + detail
    } else {
      try {
        await savePendingVisit(visitData)
        savedSnack.value = true
        savedCount.value++
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
    const { data } = await api.get('/apiaries/' + (props.apiaryId || route.params.apiaryId) + '/hives/editable')
    hives.value = data
  } catch {}
  loading.value = false
})

onUnmounted(() => {
  window.removeEventListener('online', onOnline)
  window.removeEventListener('offline', onOffline)
  recognition?.stop()
})
</script>

<style scoped>
.live-mode {
  max-width: 500px;
  margin: 0 auto;
  padding: 16px;
}
</style>
