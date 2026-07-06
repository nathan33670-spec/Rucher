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
      <p class="text-caption text-medium-emphasis mb-3">
        Touchez <v-icon size="14">mdi-calendar-plus</v-icon> pour planifier une visite un jour donné.
        Vos jours planifiés sont enregistrés et modifiables à tout moment.
      </p>

      <v-card v-for="d in days" :key="d.iso" class="mb-2" :color="planned.has(d.iso) ? 'blue-lighten-5' : undefined"
        variant="outlined" border>
        <div class="d-flex align-center pa-3 ga-3 flex-wrap">
          <div class="text-h5">{{ wmo(d.code).emoji }}</div>
          <div style="min-width: 120px;">
            <div class="font-weight-bold text-capitalize">{{ d.label }}</div>
            <div class="text-caption text-medium-emphasis">{{ d.tmin }}–{{ d.tmax }}°C</div>
          </div>
          <v-chip :color="d.color" size="small" variant="flat" class="text-white">{{ d.verdict }}</v-chip>
          <div class="text-body-2 text-medium-emphasis flex-grow-1">
            <template v-if="d.window">🕒 Créneau : <b>{{ d.window }}</b></template>
            <template v-else>Pas de créneau idéal</template>
            <span class="ml-2">💧 {{ d.maxRain }}% · 💨 {{ d.maxWind }} km/h</span>
          </div>
          <v-btn
            :color="planned.has(d.iso) ? 'primary' : 'grey'"
            :variant="planned.has(d.iso) ? 'flat' : 'tonal'"
            size="small"
            class="text-none"
            :prepend-icon="planned.has(d.iso) ? 'mdi-calendar-check' : 'mdi-calendar-plus'"
            @click="togglePlan(d.iso)"
          >
            {{ planned.has(d.iso) ? 'Planifiée' : 'Planifier' }}
          </v-btn>
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
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import api from '../services/api'

// Bois-d'Arcy (78)
const LAT = 48.80
const LON = 2.02
const API = `https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}`
  + `&timezone=Europe%2FParis&forecast_days=7`
  + `&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m`
  + `&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code`

const loading = ref(false)
const error = ref('')
const current = ref(null)
const hourly = ref([])
const plans = ref([])                 // visites planifiées (backend)
const planned = reactive(new Set())   // ensemble des dates ISO planifiées

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

// Regroupe les prévisions horaires par jour et calcule le meilleur créneau
const days = computed(() => {
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

    // Heures « idéales » : journée 10-18h, 15-30°C, pluie < 30%, vent < 25 km/h
    const ideal = hours.filter((h) => {
      const hr = hourOf(h.time)
      return hr >= 10 && hr <= 18 && h.temp >= 15 && h.temp <= 30 && h.rain < 30 && h.wind < 25
    })
    let window = null
    if (ideal.length) {
      const run = [ideal[0]]
      for (let i = 1; i < ideal.length; i++) {
        if (hourOf(ideal[i].time) === hourOf(ideal[i - 1].time) + 1) run.push(ideal[i])
        else break
      }
      window = `${hourOf(run[0].time)}h–${hourOf(run[run.length - 1].time) + 1}h`
    }

    let verdict, color
    if (ideal.length >= 2) { verdict = 'Idéal'; color = 'green' }
    else if (maxRain < 50 && tmax >= 12 && maxWind < 35) { verdict = 'Correct'; color = 'amber-darken-2' }
    else { verdict = 'Déconseillé'; color = 'red' }

    out.push({
      iso,
      label: new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'short' }),
      tmin, tmax, maxRain, maxWind, code: noon?.code, window, verdict, color,
    })
  }
  return out.slice(0, 7)
})

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(API)
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

onMounted(() => { load(); loadPlans() })
</script>

<style scoped>
.current-card { background: linear-gradient(135deg, #4FC3F7, #0288D1); color: #fff; }
</style>
