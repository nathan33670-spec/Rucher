<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h2>Journal d'activité</h2>
    </div>

    <FilterBar
      v-model="filters" :fields="filterFields"
      :total="logs.length" :shown="filteredLogs.length" item-label="entrée"
    />

    <v-timeline density="compact" side="end">
      <v-timeline-item v-for="log in filteredLogs" :key="log.id" :dot-color="actionColor(log.action)" size="small">
        <v-card density="compact" class="pa-2">
          <div class="d-flex align-center">
            <v-icon size="small" class="mr-2">{{ actionIcon(log.action) }}</v-icon>
            <strong>{{ log.user_name || 'Système' }}</strong>
            <v-spacer />
            <span class="text-caption r-muted">{{ new Date(log.created_at).toLocaleString('fr-FR') }}</span>
          </div>
          <div class="text-body-2 mt-1">
            {{ actionLabel(log.action) }} — {{ log.entity_type }} #{{ log.entity_id }}
          </div>
          <div v-if="log.details" class="text-caption r-muted mt-1">{{ log.details }}</div>
        </v-card>
      </v-timeline-item>
    </v-timeline>

    <div v-if="!filteredLogs.length" class="text-center r-muted pa-8">
      {{ logs.length ? 'Aucune entrée ne correspond à ces filtres' : 'Aucune entrée dans le journal' }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FilterBar from '../components/FilterBar.vue'
import api from '../services/api'
import { toastError, apiError } from '../services/toast'

const logs = ref([])

// ─── Filtres ──────────────────────────────────────────────
// Le type d'objet ne suffisait pas : « qu'a fait Untel le 3 » demandait de
// remonter tout le journal à la main.
const filters = ref({ entity: null, user: null, action: null, from: null, to: null })
const uniqL = (l) => [...new Set(l.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b)))
const ENTITY_LABELS = {
  visit: 'Visites', hive: 'Ruches', apiary: 'Ruchers', user: 'Utilisateurs',
  inventory_item: 'Inventaire', inventory_movement: 'Mouvements de stock',
  transaction: 'Trésorerie', sanitary_record: 'Sanitaire',
  honey_harvest: 'Récoltes', honey_jar: 'Pots', honey_sale: 'Ventes',
  event: 'Événements', settings: 'Réglages', doc: 'Documentation',
}

const filterFields = computed(() => [
  { key: 'entity', label: 'Type', type: 'select', icon: 'mdi-shape-outline',
    items: uniqL(logs.value.map((l) => l.entity_type))
      .map((v) => ({ title: ENTITY_LABELS[v] || v, value: v })) },
  { key: 'user', label: 'Par qui', type: 'select', icon: 'mdi-account',
    items: uniqL(logs.value.map((l) => l.user_name)).map((v) => ({ title: v, value: v })) },
  { key: 'action', label: 'Action', type: 'select', icon: 'mdi-gesture-tap',
    items: uniqL(logs.value.map((l) => l.action))
      .map((v) => ({ title: actionLabel(v), value: v })) },
  { key: 'from', label: 'Du', type: 'date' },
  { key: 'to', label: 'Au', type: 'date' },
])

const filteredLogs = computed(() => {
  const f = filters.value
  return logs.value.filter((l) => {
    if (f.entity && l.entity_type !== f.entity) return false
    if (f.user && l.user_name !== f.user) return false
    if (f.action && l.action !== f.action) return false
    const d = (l.created_at || '').substring(0, 10)
    if (f.from && d < f.from) return false
    if (f.to && d > f.to) return false
    return true
  })
})

function actionColor(a) {
  return { create: 'success', update: 'info', delete: 'error' }[a] || 'grey'
}
function actionIcon(a) {
  return { create: 'mdi-plus-circle', update: 'mdi-pencil-circle', delete: 'mdi-delete-circle' }[a] || 'mdi-information'
}
function actionLabel(a) {
  return { create: 'Création', update: 'Modification', delete: 'Suppression', password_reset: 'Reset MDP', import_csv: 'Import CSV' }[a] || a
}

async function load() {
  // Le journal est chargé une fois puis filtré à l'écran : les filtres
  // s'enchaînent sans aller-retour serveur.
  try {
    const { data } = await api.get('/audit/', { params: { limit: 300 } })
    logs.value = data
  } catch (e) {
    toastError(apiError(e, "Chargement du journal impossible"))
  }
}

onMounted(load)
</script>
