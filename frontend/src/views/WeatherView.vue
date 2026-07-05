<template>
  <div style="max-width: 760px; margin: 0 auto;">
    <div class="d-flex align-center mb-4">
      <h2>Météo du rucher</h2>
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
          <div class="text-h1 mr-4">{{ wmo(current.weather_code).emoji }}</div>
          <div>
            <div class="text-h3 font-weight-bold">{{ Math.round(current.temperature_2m) }}°C</div>
            <div class="text-body-2">{{ wmo(current.weather_code).label }} · ressenti {{ Math.round(current.apparent_temperature) }}°C</div>
          </div>
        </div>
        <v-row class="mt-4 text-center" no-gutters>
          <v-col v-for="s in stats" :key="s.label">
            <v-icon color="white">{{ s.icon }}</v-icon>
            <div class="text-h6 font-weight-bold">{{ s.value }}</div>
            <div class="text-caption">{{ s.label }}</div>
          </v-col>
        </v-row>
      </v-card>

      <!-- Créneau optimal de visite -->
      <v-card class="mb-4 pa-4" :color="best ? 'green-lighten-5' : 'orange-lighten-5'" flat border>
        <div class="d-flex align-center mb-2">
          <v-icon :color="best ? 'green-darken-2' : 'orange-darken-2'" class="mr-2">mdi-calendar-check</v-icon>
          <span class="text-subtitle-1 font-weight-bold">Créneau optimal de visite</span>
        </div>
        <template v-if="best">
          <div class="text-h6 font-weight-bold text-green-darken-3">{{ best.label }}</div>
          <div class="text-body-2 mt-1">
            {{ best.tmin }}–{{ best.tmax }}°C · pluie {{ best.rain }}% · vent {{ best.wind }} km/h
          </div>
          <p class="text-caption text-medium-emphasis mt-2 mb-0">
            Conditions douces, sèches et peu ventées : les butineuses sont dehors,
            la colonie est calme — idéal pour ouvrir les ruches.
          </p>
        </template>
        <template v-else>
          <div class="text-body-2">
            Aucun créneau idéal dans les 3 prochains jours.
            Privilégiez un moment <b>doux (≥ 15°C), sec et peu venté</b>, en milieu de journée.
          </div>
        </template>
      </v-card>

      <!-- Prévisions prochaines heures -->
      <v-card flat border class="pa-2">
        <div class="text-subtitle-2 font-weight-bold px-2 py-1">Prochaines heures</div>
        <div class="hourly-scroll">
          <div v-for="h in upcoming" :key="h.time" class="hour-cell" :class="{ ideal: h.ideal }">
            <div class="text-caption">{{ h.hourLabel }}</div>
            <div class="text-h6">{{ wmo(h.code).emoji }}</div>
            <div class="font-weight-bold">{{ Math.round(h.temp) }}°</div>
            <div class="text-caption text-blue">{{ h.rain }}%</div>
          </div>
        </div>
      </v-card>
    </template>

    <div v-else-if="loading" class="text-center pa-8">
      <v-progress-circular indeterminate color="primary" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Bois-d'Arcy (78) — canal de la Croix Bonnet
const LAT = 48.80
const LON = 2.02
const API = `https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}`
  + `&timezone=Europe%2FParis&forecast_days=3`
  + `&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m`
  + `&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code`

const loading = ref(false)
const error = ref('')
const current = ref(null)
const hourly = ref([])

// Table WMO simplifiée → emoji + libellé
function wmo(code) {
  const m = {
    0: ['☀️', 'Ciel dégagé'], 1: ['🌤️', 'Peu nuageux'], 2: ['⛅', 'Partiellement nuageux'], 3: ['☁️', 'Couvert'],
    45: ['🌫️', 'Brouillard'], 48: ['🌫️', 'Brouillard givrant'],
    51: ['🌦️', 'Bruine légère'], 53: ['🌦️', 'Bruine'], 55: ['🌧️', 'Bruine dense'],
    61: ['🌦️', 'Pluie faible'], 63: ['🌧️', 'Pluie'], 65: ['🌧️', 'Pluie forte'],
    71: ['🌨️', 'Neige faible'], 73: ['🌨️', 'Neige'], 75: ['❄️', 'Neige forte'],
    80: ['🌦️', 'Averses'], 81: ['🌧️', 'Averses'], 82: ['⛈️', 'Fortes averses'],
    95: ['⛈️', 'Orage'], 96: ['⛈️', 'Orage grêleux'], 99: ['⛈️', 'Orage violent'],
  }
  const [emoji, label] = m[code] || ['🌡️', 'Conditions variables']
  return { emoji, label }
}

const stats = computed(() => current.value ? [
  { icon: 'mdi-water-percent', value: current.value.relative_humidity_2m + '%', label: 'Hygrométrie' },
  { icon: 'mdi-weather-rainy', value: current.value.precipitation + ' mm', label: 'Pluie' },
  { icon: 'mdi-weather-windy', value: Math.round(current.value.wind_speed_10m) + ' km/h', label: 'Vent' },
] : [])

// Heures à venir (limitées à ~24h pour l'affichage)
const upcoming = computed(() => {
  const now = Date.now()
  return hourly.value
    .filter((h) => new Date(h.time).getTime() >= now - 3600e3)
    .slice(0, 24)
    .map((h) => ({
      ...h,
      hourLabel: new Date(h.time).getHours() + 'h',
    }))
})

// Un créneau est « idéal » : journée (10-18h), 15-30°C, pluie < 30%, vent < 25 km/h
function isIdeal(h) {
  const hr = new Date(h.time).getHours()
  return hr >= 10 && hr <= 18 && h.temp >= 15 && h.temp <= 30 && h.rain < 30 && h.wind < 25
}

const best = computed(() => {
  const now = Date.now()
  const future = hourly.value.filter((h) => new Date(h.time).getTime() >= now)
  // Première plage contiguë d'heures idéales (≥ 2h)
  let run = []
  for (const h of future) {
    if (isIdeal(h)) {
      run.push(h)
    } else if (run.length >= 2) {
      break
    } else {
      run = []
    }
  }
  if (run.length < 2) return null
  const start = new Date(run[0].time)
  const end = new Date(run[run.length - 1].time)
  const day = start.toLocaleDateString('fr-FR', { weekday: 'long' })
  const label = `${day.charAt(0).toUpperCase() + day.slice(1)} ${start.getHours()}h–${end.getHours()}h`
  return {
    label,
    tmin: Math.round(Math.min(...run.map((h) => h.temp))),
    tmax: Math.round(Math.max(...run.map((h) => h.temp))),
    rain: Math.max(...run.map((h) => h.rain)),
    wind: Math.round(Math.max(...run.map((h) => h.wind))),
  }
})

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
      time: t,
      temp: H.temperature_2m[i],
      humidity: H.relative_humidity_2m[i],
      rain: H.precipitation_probability[i] ?? 0,
      wind: H.wind_speed_10m[i],
      code: H.weather_code[i],
      ideal: false,
    })).map((h) => ({ ...h, ideal: isIdeal(h) }))
  } catch (e) {
    error.value = "Météo indisponible (vérifiez la connexion Internet)."
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.current-card {
  background: linear-gradient(135deg, #4FC3F7, #0288D1);
  color: #fff;
}
.hourly-scroll { display: flex; gap: 4px; overflow-x: auto; padding: 8px; }
.hour-cell {
  flex: 0 0 auto; width: 62px; text-align: center; padding: 8px 4px;
  border-radius: 10px; background: #f5f5f5;
}
.hour-cell.ideal { background: #C8E6C9; }
</style>
