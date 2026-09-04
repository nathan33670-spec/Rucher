<template>
  <div style="max-width: 820px; margin: 0 auto;">
    <div class="d-flex align-center mb-1">
      <h2>Météo &amp; planification</h2>
      <v-spacer />
      <v-btn icon size="small" variant="text" :loading="loading" @click="load"><v-icon>mdi-refresh</v-icon></v-btn>
    </div>
    <p class="text-caption text-medium-emphasis mb-4">
      <v-icon size="14">mdi-map-marker</v-icon> Bois-d'Arcy (78) — canal de la Croix Bonnet
    </p>

    <v-alert v-if="error" type="error" density="compact" class="mb-4">{{ error }}</v-alert>

    <!-- Rappel des critères en vigueur (+ réglage pour l'administrateur).
         Volontairement hors du bloc de prévisions : l'administrateur doit
         pouvoir régler les critères même si le service météo est injoignable. -->
    <v-card class="mb-4 pa-3 criteria-bar" :elevation="0">
      <div class="d-flex align-center ga-2 flex-wrap">
        <v-icon size="16" color="primary">mdi-tune-variant</v-icon>
        <span class="text-caption">
          <b>Créneau idéal</b> : {{ criteria.ideal.hour_start }}h–{{ criteria.ideal.hour_end }}h,
          {{ criteria.ideal.temp_min }}–{{ criteria.ideal.temp_max }}°C,
          pluie &lt; {{ criteria.ideal.rain_max }}%, vent &lt; {{ criteria.ideal.wind_max }} km/h,
          au moins {{ criteria.ideal.min_hours }} h dans la journée
        </span>
        <v-chip size="x-small" variant="tonal" :color="personalCriteria ? 'accent' : 'secondary'">
          <v-icon start size="12">{{ personalCriteria ? 'mdi-account' : 'mdi-account-group' }}</v-icon>
          {{ personalCriteria ? 'Mes critères' : "Critères de l'association" }}
        </v-chip>
        <v-spacer />
        <!-- Chaque adhérent règle ses propres conditions de sortie : le
             matériel, la disponibilité et la tolérance au vent ne sont pas
             les mêmes pour tout le monde. -->
        <v-btn
          size="small" variant="tonal" color="primary"
          prepend-icon="mdi-account-cog-outline"
          @click="openCriteria('mine')"
        >
          Mes critères
        </v-btn>
        <v-btn
          v-if="auth.isAdmin"
          size="small" variant="text" color="secondary"
          prepend-icon="mdi-cog-outline"
          @click="openCriteria('asso')"
        >
          Critères de l'association
        </v-btn>
      </div>
    </v-card>

    <template v-if="current">
      <!-- Conditions actuelles -->
      <v-card class="mb-4 pa-4 current-card" flat>
        <div class="d-flex align-center">
          <div class="text-h2 mr-4">{{ wmo(current.weather_code).emoji }}</div>
          <div>
            <div class="text-h3 font-weight-bold">{{ Math.round(current.temperature_2m) }}°C</div>
            <div class="text-body-2">{{ wmo(current.weather_code).label }} · ressenti {{ Math.round(current.apparent_temperature) }}°C</div>
          </div>
          <v-spacer />
          <div class="text-right d-none d-sm-block">
            <div><v-icon size="18" color="white">mdi-water-percent</v-icon> {{ current.relative_humidity_2m }}%</div>
            <div><v-icon size="18" color="white">mdi-weather-rainy</v-icon> {{ current.precipitation }} mm</div>
            <div><v-icon size="18" color="white">mdi-weather-windy</v-icon> {{ Math.round(current.wind_speed_10m) }} km/h</div>
          </div>
        </div>
      </v-card>

      <!-- Meilleurs créneaux sur 7 jours + planification -->
      <div class="d-flex align-center mb-2">
        <v-icon color="primary" class="mr-2">mdi-calendar-week</v-icon>
        <span class="text-subtitle-1 font-weight-bold">Meilleurs créneaux de visite (7 jours)</span>
      </div>
      <p class="text-caption r-muted mb-3">
        Touchez <v-icon size="14">mdi-calendar-plus</v-icon> pour planifier une visite un jour donné.
        Vos jours planifiés sont enregistrés et modifiables à tout moment.
      </p>

      <v-card
        v-for="d in days" :key="d.iso"
        class="mb-2 day-card"
        :class="{ 'day-card--planned': planned.has(d.iso) }"
      >
        <div class="d-flex align-center pa-3 ga-3 flex-wrap">
          <div class="text-h5">{{ wmo(d.code).emoji }}</div>
          <div style="min-width: 128px;">
            <div class="font-weight-bold text-capitalize">{{ d.label }}</div>
            <div class="text-caption r-muted">{{ d.tmin }}–{{ d.tmax }}°C</div>
          </div>
          <v-chip :color="d.color" size="small" variant="flat" class="text-white">{{ d.verdict }}</v-chip>
          <div class="text-caption r-muted flex-grow-1">
            <v-icon size="13">mdi-weather-rainy</v-icon> {{ d.maxRain }}%
            <v-icon size="13" class="ml-2">mdi-weather-windy</v-icon> {{ d.maxWind }} km/h
          </div>
          <div class="d-flex ga-2 flex-wrap">
            <v-btn
              :color="planned.has(d.iso) ? 'primary' : undefined"
              :variant="planned.has(d.iso) ? 'flat' : 'tonal'"
              size="small"
              :prepend-icon="planned.has(d.iso) ? 'mdi-calendar-check' : 'mdi-calendar-plus'"
              @click="togglePlan(d.iso)"
            >
              {{ planned.has(d.iso) ? 'Planifiée' : 'Planifier' }}
            </v-btn>
            <!-- Sortie collective : visible pour les responsables uniquement -->
            <v-btn
              v-if="canPlanEvent"
              size="small" variant="tonal" color="secondary"
              prepend-icon="mdi-account-group"
              title="Créer une sortie pour toute l'association"
              @click="openEvent(d)"
            >
              Sortie collective
            </v-btn>
          </div>
        </div>

        <!-- Heures idéales : toutes les plages de la journée, pas seulement la première -->
        <v-divider />
        <div class="px-3 py-2 d-flex align-center ga-2 flex-wrap">
          <span class="text-caption font-weight-bold r-muted">
            <v-icon size="14">mdi-clock-outline</v-icon>
            Heures idéales
          </span>
          <template v-if="d.windows.length">
            <v-chip
              v-for="w in d.windows" :key="w.start"
              size="small" color="success" variant="tonal"
            >
              {{ w.label }}
              <span class="ml-1 font-weight-regular">· {{ w.temp }}°C</span>
            </v-chip>
            <span class="text-caption r-muted">
              ({{ d.idealCount }} h au total)
            </span>
          </template>
          <span v-else class="text-caption r-muted">Aucune heure ne remplit les critères</span>
        </div>
      </v-card>

      <!-- Mes visites planifiées -->
      <v-card v-if="plans.length" class="mt-4" variant="tonal" color="primary">
        <v-card-item>
          <v-card-title class="text-subtitle-1 font-weight-bold">
            <v-icon start>mdi-calendar-star</v-icon> Mes visites planifiées
          </v-card-title>
        </v-card-item>
        <v-card-text>
          <div v-for="p in plans" :key="p.plan_date" class="d-flex align-center ga-2 mb-2 flex-wrap">
            <v-icon size="18">mdi-calendar</v-icon>
            <b style="min-width: 150px;" class="text-capitalize">{{ formatDate(p.plan_date) }}</b>
            <v-text-field
              :model-value="p.note || ''"
              @update:model-value="p._note = $event"
              @blur="saveNote(p)"
              placeholder="Note (facultatif)"
              density="compact" variant="outlined" hide-details
              class="flex-grow-1" style="min-width: 160px;"
            />
            <v-btn icon size="x-small" variant="text" color="error" @click="togglePlan(p.plan_date)"><v-icon>mdi-close</v-icon></v-btn>
          </div>
        </v-card-text>
      </v-card>
    </template>

    <div v-else-if="loading" class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <!-- Création d'une sortie collective depuis un créneau météo -->
    <v-dialog v-model="showEvent" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="secondary">mdi-calendar-star</v-icon>
          Nouvelle sortie collective
        </v-card-title>
        <v-card-text>
          <p v-if="eventDay" class="text-body-2 r-muted mb-4">
            <b class="text-capitalize">{{ eventDay.label }}</b> — journée classée
            <b>{{ eventDay.verdict.toLowerCase() }}</b>.
            <template v-if="eventDay.windows.length">
              Créneaux idéaux :
              <b>{{ eventDay.windows.map(w => w.label).join(', ') }}</b>.
            </template>
            <template v-else>Aucun créneau idéal ce jour-là.</template>
          </p>

          <v-text-field v-model="eventForm.title" label="Intitulé" density="compact" class="mb-1" />
          <v-row dense>
            <v-col cols="6">
              <v-text-field v-model="eventForm.start" label="Début" type="time" density="compact" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model="eventForm.end" label="Fin" type="time" density="compact" />
            </v-col>
          </v-row>
          <v-select
            v-if="apiaries.length"
            v-model="eventForm.location"
            :items="apiaryNames"
            label="Lieu"
            density="compact"
            class="mb-1"
          />
          <v-text-field v-else v-model="eventForm.location" label="Lieu" density="compact" class="mb-1" />
          <v-textarea v-model="eventForm.description" label="Description" rows="2" density="compact" />

          <v-alert type="info" variant="tonal" density="compact" class="mt-1">
            Les adhérents seront prévenus par notification et pourront indiquer
            s'ils viennent.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showEvent = false">Annuler</v-btn>
          <v-btn color="primary" :loading="savingEvent" @click="createEvent">Créer la sortie</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Réglage des critères — administrateur uniquement -->
    <v-dialog v-model="showCriteria" max-width="560">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">
            {{ criteriaScope === 'mine' ? 'mdi-account-cog-outline' : 'mdi-tune-variant' }}
          </v-icon>
          {{ criteriaScope === 'mine' ? 'Mes critères de sortie' : "Critères de l'association" }}
        </v-card-title>
        <v-card-text>
          <p class="text-body-2 r-muted mb-4">
            Ces critères déterminent si une journée est classée <b>Idéale</b>, <b>Correcte</b>
            ou <b>Déconseillée</b>, et quelles heures sont proposées pour la visite.
          </p>
          <v-alert
            :type="criteriaScope === 'mine' ? 'info' : 'warning'"
            variant="tonal" density="compact" class="mb-4"
          >
            <template v-if="criteriaScope === 'mine'">
              Ces réglages ne concernent <b>que votre affichage</b>. Sans réglage
              personnel, ce sont les critères de l'association qui s'appliquent.
            </template>
            <template v-else>
              Ces réglages s'appliquent à <b>tous les adhérents</b> qui n'ont pas
              défini les leurs.
            </template>
          </v-alert>

          <div class="text-subtitle-2 font-weight-bold mb-2">
            <v-chip size="small" color="success" variant="tonal" class="mr-2">Idéal</v-chip>
            Conditions d'ouverture des ruches
          </div>
          <v-row dense>
            <v-col cols="6">
              <v-text-field v-model.number="criteriaForm.ideal.hour_start" label="Heure de début" type="number" min="0" max="23" suffix="h" density="compact" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model.number="criteriaForm.ideal.hour_end" label="Heure de fin" type="number" min="0" max="23" suffix="h" density="compact" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model.number="criteriaForm.ideal.temp_min" label="Température mini" type="number" suffix="°C" density="compact" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model.number="criteriaForm.ideal.temp_max" label="Température maxi" type="number" suffix="°C" density="compact" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model.number="criteriaForm.ideal.rain_max" label="Pluie maxi" type="number" min="0" max="100" suffix="%" density="compact" />
            </v-col>
            <v-col cols="6">
              <v-text-field v-model.number="criteriaForm.ideal.wind_max" label="Vent maxi" type="number" min="0" suffix="km/h" density="compact" />
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model.number="criteriaForm.ideal.min_hours"
                label="Heures idéales requises pour classer la journée « Idéale »"
                type="number" min="1" max="12" suffix="h" density="compact"
              />
            </v-col>
          </v-row>

          <v-divider class="my-3" />

          <div class="text-subtitle-2 font-weight-bold mb-2">
            <v-chip size="small" color="warning" variant="tonal" class="mr-2">Correct</v-chip>
            Journée acceptable à défaut d'idéale
          </div>
          <v-row dense>
            <v-col cols="4">
              <v-text-field v-model.number="criteriaForm.ok.temp_min" label="Temp. maxi ≥" type="number" suffix="°C" density="compact" />
            </v-col>
            <v-col cols="4">
              <v-text-field v-model.number="criteriaForm.ok.rain_max" label="Pluie &lt;" type="number" min="0" max="100" suffix="%" density="compact" />
            </v-col>
            <v-col cols="4">
              <v-text-field v-model.number="criteriaForm.ok.wind_max" label="Vent &lt;" type="number" min="0" suffix="km/h" density="compact" />
            </v-col>
          </v-row>
          <p class="text-caption r-muted mt-2">
            En dehors de ces conditions, la journée est classée « Déconseillée ».
          </p>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" :loading="savingCriteria" @click="resetCriteria">
            {{ criteriaScope === 'mine' ? "Utiliser ceux de l'association" : 'Valeurs par défaut' }}
          </v-btn>
          <v-spacer />
          <v-btn @click="showCriteria = false">Annuler</v-btn>
          <v-btn color="primary" :loading="savingCriteria" @click="saveCriteria">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="showCriteriaMsg" :color="msgIsError ? 'error' : 'success'" timeout="3500">{{ criteriaMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { apiError } from '../services/toast'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

// Bois-d'Arcy (78)
const LAT = 48.80
const LON = 2.02
const API = `https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}`
  + `&timezone=Europe%2FParis&forecast_days=7`
  + `&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m`
  + `&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code`

const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const current = ref(null)
const hourly = ref([])
const plans = ref([])                 // visites planifiées (backend)
const planned = reactive(new Set())   // ensemble des dates ISO planifiées

// ─── Critères « idéal / correct » (réglables par l'administrateur) ───
const DEFAULT_CRITERIA = {
  ideal: { hour_start: 10, hour_end: 18, temp_min: 15, temp_max: 30, rain_max: 30, wind_max: 25, min_hours: 2 },
  ok: { temp_min: 12, rain_max: 50, wind_max: 35 },
}
// Copie profonde d'un objet de données simple. `structuredClone` échouerait :
// une valeur portée par un `ref` est un proxy réactif, non clonable.
function clone(o) { return JSON.parse(JSON.stringify(o)) }

const criteria = ref(clone(DEFAULT_CRITERIA))
// Vrai lorsque l'adhérent a défini ses propres critères (sinon : ceux de l'asso).
const personalCriteria = ref(false)
const showCriteria = ref(false)
// 'mine' = préférences personnelles · 'asso' = référence de l'association.
const criteriaScope = ref('mine')
const criteriaForm = ref(clone(DEFAULT_CRITERIA))
const savingCriteria = ref(false)
const criteriaMsg = ref('')
// Un même bandeau sert aux confirmations et aux échecs : la couleur suit.
const msgIsError = ref(false)
const showCriteriaMsg = computed({
  get: () => !!criteriaMsg.value,
  set: (v) => { if (!v) criteriaMsg.value = '' },
})

async function loadCriteria() {
  try {
    // Critères réellement appliqués à cet utilisateur (les siens, sinon ceux
    // de l'association), avec l'origine pour l'afficher clairement.
    const { data } = await api.get('/settings/weather/mine')
    criteria.value = data.criteria
    personalCriteria.value = data.personal
  } catch { /* valeurs par défaut conservées */ }
}

async function openCriteria(scope = 'mine') {
  criteriaScope.value = scope
  if (scope === 'asso') {
    // Toujours partir de la référence de l'association, jamais des critères
    // personnels de l'administrateur qui les modifie.
    try {
      const { data } = await api.get('/settings/weather/association')
      criteriaForm.value = clone(data)
    } catch (e) {
      msgIsError.value = true
      criteriaMsg.value = apiError(e, "Impossible de lire les critères de l'association")
      return
    }
  } else {
    criteriaForm.value = clone(criteria.value)
  }
  showCriteria.value = true
}

async function saveCriteria() {
  savingCriteria.value = true
  const mine = criteriaScope.value === 'mine'
  try {
    const { data } = await api.put(
      mine ? '/settings/weather/mine' : '/settings/weather',
      criteriaForm.value,
    )
    if (mine) {
      criteria.value = data
      personalCriteria.value = true
    } else {
      // Les critères de l'association ne s'appliquent à l'écran que si
      // l'utilisateur n'a pas les siens.
      if (!personalCriteria.value) criteria.value = data
    }
    showCriteria.value = false
    msgIsError.value = false
    criteriaMsg.value = mine ? 'Vos critères sont enregistrés' : "Critères de l'association enregistrés"
  } catch (e) {
    msgIsError.value = true; criteriaMsg.value = apiError(e, "Impossible d'enregistrer les critères")
  } finally {
    // `days` est un computed sur `criteria` : le classement des journées et la
    // liste des heures idéales se recalculent d'eux-mêmes.
    savingCriteria.value = false
  }
}

async function resetCriteria() {
  savingCriteria.value = true
  const mine = criteriaScope.value === 'mine'
  try {
    const { data } = await api.delete(mine ? '/settings/weather/mine' : '/settings/weather')
    criteria.value = data
    criteriaForm.value = clone(data)
    if (mine) personalCriteria.value = false
    msgIsError.value = false
    criteriaMsg.value = mine
      ? "Vous suivez de nouveau les critères de l'association"
      : 'Critères par défaut rétablis'
    showCriteria.value = false
  } catch (e) {
    msgIsError.value = true
    criteriaMsg.value = apiError(e, 'Échec de la réinitialisation')
  } finally {
    // `days` est un computed sur `criteria` : le classement des journées et la
    // liste des heures idéales se recalculent d'eux-mêmes.
    savingCriteria.value = false
  }
}

function wmo(code) {
  const m = {
    0: ['☀️', 'Ciel dégagé'], 1: ['🌤️', 'Peu nuageux'], 2: ['⛅', 'Partiellement nuageux'], 3: ['☁️', 'Couvert'],
    45: ['🌫️', 'Brouillard'], 48: ['🌫️', 'Brouillard givrant'],
    51: ['🌦️', 'Bruine'], 53: ['🌦️', 'Bruine'], 55: ['🌧️', 'Bruine dense'],
    61: ['🌦️', 'Pluie faible'], 63: ['🌧️', 'Pluie'], 65: ['🌧️', 'Pluie forte'],
    71: ['🌨️', 'Neige'], 73: ['🌨️', 'Neige'], 75: ['❄️', 'Neige forte'],
    80: ['🌦️', 'Averses'], 81: ['🌧️', 'Averses'], 82: ['⛈️', 'Fortes averses'],
    95: ['⛈️', 'Orage'], 96: ['⛈️', 'Orage'], 99: ['⛈️', 'Orage violent'],
  }
  const [emoji, label] = m[code] || ['🌡️', 'Variable']
  return { emoji, label }
}

function hourOf(t) { return new Date(t).getHours() }

// Regroupe des heures consécutives en plages lisibles : 10,11,12,15,16 → « 10h–13h », « 15h–17h »
function groupRanges(hours) {
  const ranges = []
  for (const h of hours) {
    const hr = hourOf(h.time)
    const last = ranges[ranges.length - 1]
    if (last && hr === last.end) last.end = hr + 1
    else ranges.push({ start: hr, end: hr + 1, hours: [] })
    ranges[ranges.length - 1].hours.push(h)
  }
  return ranges.map((r) => ({
    ...r,
    label: `${r.start}h–${r.end}h`,
    // Température moyenne de la plage, pour aider au choix.
    temp: Math.round(r.hours.reduce((s, h) => s + h.temp, 0) / r.hours.length),
  }))
}

// Regroupe les prévisions horaires par jour et calcule les créneaux idéaux
// selon les critères réglés par l'administrateur.
const days = computed(() => {
  const C = criteria.value
  const byDay = new Map()
  for (const h of hourly.value) {
    const d = h.time.slice(0, 10)
    if (!byDay.has(d)) byDay.set(d, [])
    byDay.get(d).push(h)
  }
  const out = []
  for (const [iso, hours] of byDay) {
    const daytime = hours.filter((h) => hourOf(h.time) >= 8 && hourOf(h.time) <= 19)
    const src = daytime.length ? daytime : hours
    const temps = src.map((h) => h.temp)
    const tmin = Math.round(Math.min(...temps))
    const tmax = Math.round(Math.max(...temps))
    const maxRain = Math.max(...src.map((h) => h.rain))
    const maxWind = Math.round(Math.max(...src.map((h) => h.wind)))
    const noon = hours.find((h) => hourOf(h.time) === 13) || hours[Math.floor(hours.length / 2)]

    // Heures « idéales » selon les critères configurés
    const ideal = hours.filter((h) => {
      const hr = hourOf(h.time)
      return hr >= C.ideal.hour_start && hr <= C.ideal.hour_end
        && h.temp >= C.ideal.temp_min && h.temp <= C.ideal.temp_max
        && h.rain < C.ideal.rain_max && h.wind < C.ideal.wind_max
    })
    // Toutes les plages idéales de la journée (et non plus seulement la première)
    const windows = groupRanges(ideal)

    let verdict, color
    if (ideal.length >= C.ideal.min_hours) { verdict = 'Idéal'; color = 'success' }
    else if (maxRain < C.ok.rain_max && tmax >= C.ok.temp_min && maxWind < C.ok.wind_max) { verdict = 'Correct'; color = 'warning' }
    else { verdict = 'Déconseillé'; color = 'error' }

    out.push({
      iso,
      label: new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'short' }),
      tmin, tmax, maxRain, maxWind, code: noon?.code, windows, idealCount: ideal.length, verdict, color,
    })
  }
  return out.slice(0, 7)
})

// ─── Sortie collective (admin / responsable de rucher) ────────────
const canPlanEvent = computed(() => auth.isAdmin || auth.hasRole('yard_manager'))
const showEvent = ref(false)
const savingEvent = ref(false)
const eventDay = ref(null)
const apiaries = ref([])
const apiaryNames = computed(() => apiaries.value.map(a => a.name))
const eventForm = ref({ title: '', start: '10:00', end: '12:00', location: '', description: '' })

async function loadApiaries() {
  try {
    const { data } = await api.get('/apiaries/')
    apiaries.value = data
  } catch { /* champ lieu en saisie libre */ }
}

function openEvent(d) {
  eventDay.value = d
  // Pré-remplissage à partir du meilleur créneau de la journée.
  const w = d.windows[0]
  const pad = (n) => String(n).padStart(2, '0')
  eventForm.value = {
    title: 'Sortie au rucher',
    start: w ? `${pad(w.start)}:00` : '10:00',
    end: w ? `${pad(Math.min(w.end, 23))}:00` : '12:00',
    location: apiaries.value[0]?.name || '',
    description: d.windows.length
      ? `Créneau favorable : ${d.windows.map(x => x.label).join(', ')}.`
      : '',
  }
  showEvent.value = true
}

async function createEvent() {
  if (!eventForm.value.title.trim()) {
    msgIsError.value = true; criteriaMsg.value = 'Donnez un intitulé à la sortie'
    return
  }
  savingEvent.value = true
  try {
    const iso = eventDay.value.iso
    await api.post('/events/', {
      title: eventForm.value.title.trim(),
      description: eventForm.value.description || null,
      location: eventForm.value.location || null,
      start_at: `${iso}T${eventForm.value.start}:00`,
      end_at: eventForm.value.end ? `${iso}T${eventForm.value.end}:00` : null,
    })
    // La sortie vaut aussi planification personnelle de la journée.
    if (!planned.has(iso)) await togglePlan(iso)
    showEvent.value = false
    msgIsError.value = false; criteriaMsg.value = 'Sortie créée — les adhérents sont prévenus'
  } catch (e) {
    msgIsError.value = true; criteriaMsg.value = apiError(e, 'Création de la sortie impossible')
  } finally {
    savingEvent.value = false
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    // Délai maximal : sans cela, un service météo injoignable laisse la page
    // sur un indicateur de chargement indéfiniment.
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), 12000)
    let res
    try {
      res = await fetch(API, { signal: ctrl.signal })
    } finally {
      clearTimeout(timer)
    }
    if (!res.ok) throw new Error('réseau')
    const d = await res.json()
    current.value = d.current
    const H = d.hourly
    hourly.value = H.time.map((t, i) => ({
      time: t, temp: H.temperature_2m[i], humidity: H.relative_humidity_2m[i],
      rain: H.precipitation_probability[i] ?? 0, wind: H.wind_speed_10m[i], code: H.weather_code[i],
    }))
  } catch {
    error.value = "Météo indisponible (vérifiez la connexion Internet)."
  } finally {
    loading.value = false
  }
}

// ─── Planification persistante ────────────────────────────────────
async function loadPlans() {
  try {
    const { data } = await api.get('/visit-plans/')
    plans.value = data
    planned.clear()
    data.forEach((p) => planned.add(p.plan_date))
  } catch { /* silencieux */ }
}

async function togglePlan(iso) {
  if (planned.has(iso)) {
    await api.delete('/visit-plans/' + iso)
  } else {
    await api.post('/visit-plans/', { plan_date: iso })
  }
  await loadPlans()
}

async function saveNote(p) {
  if (p._note === undefined || p._note === (p.note || '')) return
  await api.post('/visit-plans/', { plan_date: p.plan_date, note: p._note })
  await loadPlans()
}

onMounted(() => { load(); loadPlans(); loadCriteria(); loadApiaries() })
</script>

<style scoped>
.current-card {
  background: linear-gradient(135deg, #4A9FD4, #2A6C9C);
  color: #fff;
  border: none !important;
}

/* Rappel des critères : bandeau miel très discret. */
.criteria-bar {
  background: rgba(198, 138, 18, 0.07);
  border-color: rgba(198, 138, 18, 0.24) !important;
}

.day-card {
  transition: border-color 0.2s ease;
}

/* Journée planifiée : liseré miel à gauche plutôt qu'un aplat bleu. */
.day-card--planned {
  border-color: #9A6B0F !important;
  box-shadow: inset 3px 0 0 #9A6B0F;
}
</style>
