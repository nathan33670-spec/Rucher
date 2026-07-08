<template>
  <div>
    <!-- Visite rapide : ne fait défiler que mes ruches -->
    <v-btn
      block
      color="accent"
      size="x-large"
      class="text-none mb-4"
      prepend-icon="mdi-bee"
      :to="{ name: 'visit-live-mine' }"
    >
      Visite rapide de mes ruches
    </v-btn>

    <!-- Stats rapides -->
    <v-row>
      <v-col cols="6" md="3" v-for="stat in stats" :key="stat.title">
        <v-card class="text-center pa-4">
          <v-icon :color="stat.color" size="32">{{ stat.icon }}</v-icon>
          <div class="text-h5 mt-1">{{ stat.value }}</div>
          <div class="text-caption text-grey">{{ stat.title }}</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick button visite -->
    <v-card class="mt-4 pa-4">
      <v-card-title class="text-subtitle-1 d-flex align-center">
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
              class="text-none"
              prepend-icon="mdi-play-circle"
              :to="{ name: 'visit-live', params: { apiaryId: ap.id } }"
            >
              {{ ap.name }} ({{ ap.hives_count || 0 }} ruches)
            </v-btn>
          </v-col>
        </v-row>
        <p v-if="!apiaries.length" class="text-grey text-center mt-2">Aucun rucher disponible</p>
      </v-card-text>
    </v-card>

    <!-- Stats miellée -->
    <v-card class="mt-4 pa-4" v-if="honeyStats.total_kg > 0 || honeyStats.nb_harvests > 0">
      <v-card-title class="text-subtitle-1 d-flex align-center">
        <v-icon class="mr-2" color="amber-darken-3">mdi-bee-flower</v-icon>
        Production de miel {{ currentYear }}
      </v-card-title>
      <v-card-text>
        <v-row class="mb-3">
          <v-col cols="6" sm="3">
            <v-card class="text-center pa-3" color="amber" variant="tonal">
              <v-icon size="28" color="amber-darken-3">mdi-weight-kilogram</v-icon>
              <div class="text-h5 font-weight-bold">{{ honeyStats.total_kg?.toFixed(1) || 0 }} kg</div>
              <div class="text-caption">Production totale</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card class="text-center pa-3" color="green" variant="tonal">
              <v-icon size="28" color="green-darken-2">mdi-counter</v-icon>
              <div class="text-h5 font-weight-bold">{{ honeyStats.nb_harvests || 0 }}</div>
              <div class="text-caption">Récoltes</div>
            </v-card>
          </v-col>
          <v-col v-for="own in (honeyStats.by_ownership || [])" :key="own.ownership" cols="6" sm="3">
            <v-card class="text-center pa-3" :color="own.ownership === 'associative' ? 'blue' : 'orange'" variant="tonal">
              <div class="text-h5 font-weight-bold">{{ own.total_kg.toFixed(1) }} kg</div>
              <div class="text-caption">{{ own.ownership === 'associative' ? '🏛️ Associatif' : '🏠 Privé' }}</div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Par catégorie -->
        <v-row v-if="honeyStats.by_category?.length" class="mb-3">
          <v-col v-for="cat in honeyStats.by_category" :key="cat.category" cols="6" sm="3">
            <v-card variant="outlined" class="text-center pa-3">
              <div class="text-subtitle-2 font-weight-bold">{{ cat.category }}</div>
              <div class="text-h6 text-amber-darken-3">{{ cat.total_kg.toFixed(1) }} kg</div>
              <div class="text-caption text-grey">{{ cat.nb_harvests }} récolte(s)</div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Production mensuelle -->
        <div v-if="honeyStats.by_month?.length">
          <div class="text-subtitle-2 mb-2">Production mensuelle (kg)</div>
          <div class="d-flex align-end ga-1" style="height:120px;">
            <div v-for="m in monthlyData" :key="m.month" class="d-flex flex-column align-center" style="flex:1;">
              <div class="text-caption font-weight-bold mb-1" v-if="m.kg > 0">{{ m.kg.toFixed(0) }}</div>
              <div :style="{ height: m.height + 'px', background: '#FFC107', borderRadius: '4px 4px 0 0', width: '100%', minWidth: '20px' }" />
              <div class="text-caption mt-1">{{ m.label }}</div>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Alertes actives -->
    <v-card class="mt-4" v-if="activeAlerts.length">
      <v-card-title class="text-error">
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
      <v-card-title class="text-warning">
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
const currentYear = new Date().getFullYear()

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
    const [apiariesRes, visitsRes, alertsRes, honeyRes] = await Promise.all([
      api.get('/apiaries/'),
      api.get('/visits/?limit=20'),
      api.get('/inventory/alerts'),
      api.get('/honey/stats'),
    ])

    const apiariesData = apiariesRes.data
    apiaries.value = apiariesData
    const totalHives = apiariesData.reduce((sum, a) => sum + (a.hives_count || 0), 0)

    const visits = visitsRes.data
    activeAlerts.value = visits.filter((v) => v.is_alert)
    recentVisits.value = visits.slice(0, 10).map((v) => ({
      ...v,
      date: new Date(v.visited_at).toLocaleDateString('fr-FR'),
      queen: v.queen_seen ? '✅' : v.queen_seen === false ? '❌' : '—',
    }))

    stockAlerts.value = alertsRes.data
    honeyStats.value = honeyRes.data

    stats.value = [
      { title: 'Ruchers', value: apiariesData.length, icon: 'mdi-hexagon-multiple', color: 'primary' },
      { title: 'Ruches', value: totalHives, icon: 'mdi-bee', color: 'secondary' },
      { title: 'Visites (mois)', value: visits.length, icon: 'mdi-clipboard-check', color: 'success' },
      { title: 'Alertes', value: activeAlerts.value.length, icon: 'mdi-alert', color: 'error' },
    ]
  } catch (e) {
    console.error('Dashboard load error:', e)
  }
})
</script>
