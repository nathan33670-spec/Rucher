<template>
  <div>
    <!-- Visite rapide : ne fait défiler que mes ruches -->
    <v-card class="hero-card mb-5 pa-5" :elevation="0">
      <div class="d-flex flex-wrap align-center ga-4">
        <div class="flex-grow-1 min-width-0">
          <div class="text-overline hero-eyebrow">Sur le terrain</div>
          <h2 class="mb-1">Visite rapide de mes ruches</h2>
          <p class="text-body-2 r-muted mb-0">
            Parcourez vos ruches une à une et saisissez vos observations, même hors connexion.
          </p>
        </div>
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-bee"
          :to="{ name: 'visit-live-mine' }"
          class="flex-shrink-0"
        >
          Commencer
        </v-btn>
      </div>
    </v-card>

    <!-- Stats rapides -->
    <v-row dense>
      <v-col cols="6" md="3" v-for="stat in stats" :key="stat.title">
        <v-card class="pa-4 stat-card" :to="stat.to">
          <div class="d-flex align-center ga-3">
            <v-avatar :color="stat.color" variant="tonal" size="40" rounded="lg">
              <v-icon :color="stat.color" size="21">{{ stat.icon }}</v-icon>
            </v-avatar>
            <div class="min-width-0">
              <div class="r-stat-value">{{ stat.value }}</div>
              <div class="r-stat-label text-truncate">{{ stat.title }}</div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Prochains événements -->
    <v-card class="mt-4" v-if="upcomingEvents.length">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-calendar-star</v-icon>
        Prochains événements
        <v-spacer />
        <v-btn size="small" variant="text" :to="{ name: 'events' }">Tout voir</v-btn>
      </v-card-title>
      <v-list density="compact">
        <v-list-item v-for="ev in upcomingEvents" :key="ev.id" :to="{ name: 'events' }">
          <template v-slot:prepend>
            <v-icon :color="ev.my_response === 'yes' ? 'success' : ev.my_response === 'no' ? 'error' : ev.my_response === 'maybe' ? 'warning' : 'grey'">
              {{ ev.my_response ? 'mdi-calendar-check' : 'mdi-calendar-blank' }}
            </v-icon>
          </template>
          <v-list-item-title>{{ ev.title }}</v-list-item-title>
          <v-list-item-subtitle>{{ eventWhen(ev) }}{{ ev.location ? ' · ' + ev.location : '' }}</v-list-item-subtitle>
          <template v-slot:append>
            <v-chip size="x-small" color="success" variant="tonal">{{ ev.counts.yes }} <v-icon end size="12">mdi-check</v-icon></v-chip>
          </template>
        </v-list-item>
      </v-list>
    </v-card>

    <!-- Quick button visite -->
    <v-card class="mt-4 pa-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-clipboard-check</v-icon>
        Saisie rapide de visite
      </v-card-title>
      <v-card-text>
        <v-row dense>
          <v-col v-for="ap in apiaries" :key="ap.id" cols="12" sm="6" md="4">
            <v-btn
              block
              color="primary"
              variant="tonal"
              size="large"
             
              prepend-icon="mdi-play-circle"
              :to="{ name: 'visit-live', params: { apiaryId: ap.id } }"
            >
              {{ ap.name }} ({{ ap.hives_count || 0 }} ruches)
            </v-btn>
          </v-col>
        </v-row>
        <p v-if="!apiaries.length" class="r-muted text-center mt-2">Aucun rucher disponible</p>
      </v-card-text>
    </v-card>

    <!-- Stats miellée -->
    <v-card class="mt-4 pa-4" v-if="honeyStats.total_kg > 0 || honeyStats.nb_harvests > 0">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-bee-flower</v-icon>
        Production de miel {{ currentYear }}
      </v-card-title>
      <v-card-text>
        <v-row dense class="mb-4">
          <v-col cols="6" sm="3">
            <v-card class="pa-3 text-center" color="primary" variant="tonal">
              <v-icon size="24" color="primary">mdi-weight-kilogram</v-icon>
              <div class="r-stat-value mt-1">{{ honeyStats.total_kg?.toFixed(1) || 0 }} kg</div>
              <div class="r-stat-label">Production totale</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card class="pa-3 text-center" color="secondary" variant="tonal">
              <v-icon size="24" color="secondary">mdi-counter</v-icon>
              <div class="r-stat-value mt-1">{{ honeyStats.nb_harvests || 0 }}</div>
              <div class="r-stat-label">Récoltes</div>
            </v-card>
          </v-col>
          <v-col v-for="own in (honeyStats.by_ownership || [])" :key="own.ownership" cols="6" sm="3">
            <v-card class="pa-3 text-center" :color="own.ownership === 'associative' ? 'info' : 'accent'" variant="tonal">
              <v-icon size="24" :color="own.ownership === 'associative' ? 'info' : 'accent'">
                {{ own.ownership === 'associative' ? 'mdi-account-group' : 'mdi-home' }}
              </v-icon>
              <div class="r-stat-value mt-1">{{ own.total_kg.toFixed(1) }} kg</div>
              <div class="r-stat-label">{{ own.ownership === 'associative' ? 'Associatif' : 'Privé' }}</div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Par catégorie -->
        <v-row v-if="honeyStats.by_category?.length" dense class="mb-4">
          <v-col v-for="cat in honeyStats.by_category" :key="cat.category" cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-subtitle-2 font-weight-bold text-truncate">{{ cat.category }}</div>
              <div class="text-h6 font-weight-bold text-primary">{{ cat.total_kg.toFixed(1) }} kg</div>
              <div class="text-caption r-muted">{{ cat.nb_harvests }} récolte(s)</div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Production mensuelle -->
        <div v-if="honeyStats.by_month?.length">
          <div class="text-subtitle-2 mb-3">Production mensuelle (kg)</div>
          <div class="d-flex align-end ga-1 chart-row">
            <div v-for="m in monthlyData" :key="m.month" class="d-flex flex-column align-center chart-col">
              <div class="text-caption font-weight-bold mb-1 text-primary" v-if="m.kg > 0">{{ m.kg.toFixed(0) }}</div>
              <div
                class="chart-bar"
                :class="{ 'chart-bar--empty': m.kg === 0 }"
                :style="{ height: Math.max(m.height, 3) + 'px' }"
                :title="`${m.label} : ${m.kg.toFixed(1)} kg`"
              />
              <div class="text-caption r-muted mt-1">{{ m.label }}</div>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Alertes actives -->
    <v-card class="mt-4" v-if="activeAlerts.length">
      <v-card-title>
        <v-icon color="error" class="mr-2">mdi-alert</v-icon>
        Alertes actives
      </v-card-title>
      <v-list>
        <v-list-item v-for="a in activeAlerts" :key="a.id">
          <v-list-item-title>{{ a.alert_message || 'Alerte' }} — Ruche #{{ a.hive_id }}</v-list-item-title>
          <v-list-item-subtitle>{{ new Date(a.visited_at).toLocaleDateString('fr-FR') }} par {{ a.author_name }}</v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>

    <!-- Dernières visites -->
    <v-card class="mt-4">
      <v-card-title>
        <v-icon class="mr-2">mdi-history</v-icon>
        Dernières visites
      </v-card-title>
      <v-data-table
        :headers="visitHeaders"
        :items="recentVisits"
        density="compact"
        :items-per-page="5"
      />
    </v-card>

    <!-- Alertes stock -->
    <v-card class="mt-4" v-if="stockAlerts.length">
      <v-card-title>
        <v-icon color="warning" class="mr-2">mdi-package-variant-closed</v-icon>
        Stocks bas
      </v-card-title>
      <v-list density="compact">
        <v-list-item v-for="s in stockAlerts" :key="s.id">
          <v-list-item-title>{{ s.name }}</v-list-item-title>
          <template v-slot:append>
            <v-chip color="warning" size="small">{{ s.quantity }} / {{ s.threshold }}</v-chip>
          </template>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

const stats = ref([])
const apiaries = ref([])
const activeAlerts = ref([])
const recentVisits = ref([])
const stockAlerts = ref([])
const honeyStats = ref({})
const upcomingEvents = ref([])
const currentYear = new Date().getFullYear()

function eventWhen(ev) {
  return new Date(ev.start_at).toLocaleString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

const monthLabels = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc']

const monthlyData = computed(() => {
  const data = Array.from({ length: 12 }, (_, i) => ({ month: i + 1, kg: 0, label: monthLabels[i] }))
  if (honeyStats.value.by_month) {
    for (const m of honeyStats.value.by_month) data[m.month - 1].kg = m.total_kg
  }
  const maxKg = Math.max(...data.map(d => d.kg), 1)
  return data.map(d => ({ ...d, height: (d.kg / maxKg) * 100 }))
})

const visitHeaders = [
  { title: 'Date', key: 'date' },
  { title: 'Ruche', key: 'hive_id' },
  { title: 'Auteur', key: 'author_name' },
  { title: 'Reine', key: 'queen' },
  { title: 'Couvain', key: 'brood_score' },
  { title: 'Réserves', key: 'reserves_score' },
]

onMounted(async () => {
  try {
    const [apiariesRes, visitsRes, alertsRes, honeyRes, visitStatsRes] = await Promise.all([
      api.get('/apiaries/'),
      api.get('/visits/?limit=20'),
      api.get('/inventory/alerts'),
      api.get('/honey/stats'),
      api.get('/visits/stats'),
    ])

    const apiariesData = apiariesRes.data
    apiaries.value = apiariesData
    const totalHives = apiariesData.reduce((sum, a) => sum + (a.hives_count || 0), 0)

    const visits = visitsRes.data
    activeAlerts.value = visits.filter((v) => v.is_alert)
    recentVisits.value = visits.slice(0, 10).map((v) => ({
      ...v,
      date: new Date(v.visited_at).toLocaleDateString('fr-FR'),
      queen: v.queen_seen ? 'Vue' : v.queen_seen === false ? 'Non vue' : '—',
    }))

    stockAlerts.value = alertsRes.data
    honeyStats.value = honeyRes.data

    stats.value = [
      { title: 'Ruchers', value: apiariesData.length, icon: 'mdi-hexagon-multiple', color: 'primary', to: { name: 'apiaries' } },
      { title: 'Ruches', value: totalHives, icon: 'mdi-bee', color: 'secondary', to: { name: 'apiaries' } },
      { title: 'Visites ce mois', value: visitStatsRes.data.month, icon: 'mdi-clipboard-check', color: 'success', to: { name: 'visits' } },
      { title: 'Alertes', value: activeAlerts.value.length, icon: 'mdi-alert', color: 'error', to: { name: 'visits' } },
    ]
  } catch (e) {
    console.error('Dashboard load error:', e)
  }

  // Prochains événements (chargement séparé — ne bloque pas le reste du tableau de bord)
  try {
    const { data } = await api.get('/events/')
    const now = new Date()
    upcomingEvents.value = data
      .filter(e => new Date(e.end_at || e.start_at) >= now)
      .slice(0, 3)
  } catch (e) {
    console.error('Events load error:', e)
  }
})
</script>

<style scoped>
/* Bandeau d'accueil : met en avant l'action principale sans crier. */
.hero-card {
  background: linear-gradient(135deg, rgba(198, 138, 18, 0.13), rgba(198, 138, 18, 0.03) 62%, transparent);
  border-radius: 18px !important;
}

.hero-eyebrow {
  font-size: 0.6875rem;
  letter-spacing: 0.11em;
  line-height: 1.4;
  color: #9A6B0F;
  opacity: 0.9;
}

/* Tuiles de statistiques : réaction discrète au survol. */
.stat-card {
  height: 100%;
}

@media (hover: hover) {
  .stat-card:hover {
    transform: translateY(-2px);
  }
}

.stat-card {
  transition: transform 0.2s cubic-bezier(0.22, 0.61, 0.36, 1),
    box-shadow 0.2s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.min-width-0 {
  min-width: 0;
}

/* Histogramme de production : barres miel, dégradé vertical. */
.chart-row {
  height: 132px;
}

.chart-col {
  flex: 1;
  min-width: 0;
}

.chart-bar {
  width: 100%;
  min-width: 14px;
  border-radius: 5px 5px 0 0;
  background: linear-gradient(180deg, #D89A1E, #9A6B0F);
  transition: filter 0.2s ease;
}

@media (hover: hover) {
  .chart-bar:hover {
    filter: brightness(1.12);
  }
}

.chart-bar--empty {
  background: rgba(93, 64, 55, 0.12);
}
</style>
