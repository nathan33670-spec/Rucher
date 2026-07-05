<template>
  <div>
    <div class="d-flex align-center mb-4">
      <h2>Journal d'activité</h2>
      <v-spacer />
      <v-select v-model="filter" :items="filterOptions" item-title="title" item-value="value" label="Filtrer" density="compact" style="max-width:200px" clearable @update:model-value="load" />
    </div>

    <v-timeline density="compact" side="end">
      <v-timeline-item v-for="log in logs" :key="log.id" :dot-color="actionColor(log.action)" size="small">
        <v-card density="compact" class="pa-2">
          <div class="d-flex align-center">
            <v-icon size="small" class="mr-2">{{ actionIcon(log.action) }}</v-icon>
            <strong>{{ log.user_name || 'Système' }}</strong>
            <v-spacer />
            <span class="text-caption text-grey">{{ new Date(log.created_at).toLocaleString('fr-FR') }}</span>
          </div>
          <div class="text-body-2 mt-1">
            {{ actionLabel(log.action) }} — {{ log.entity_type }} #{{ log.entity_id }}
          </div>
          <div v-if="log.details" class="text-caption text-grey mt-1">{{ log.details }}</div>
        </v-card>
      </v-timeline-item>
    </v-timeline>

    <div v-if="!logs.length" class="text-center text-grey pa-8">Aucune entrée dans le journal</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const logs = ref([])
const filter = ref(null)
const filterOptions = [
  { title: 'Tout', value: null },
  { title: 'Visites', value: 'visit' },
  { title: 'Ruches', value: 'hive' },
  { title: 'Ruchers', value: 'apiary' },
  { title: 'Utilisateurs', value: 'user' },
  { title: 'Inventaire', value: 'inventory_item' },
  { title: 'Trésorerie', value: 'transaction' },
  { title: 'Sanitaire', value: 'sanitary_record' },
]

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
  const params = {}
  if (filter.value) params.entity_type = filter.value
  const { data } = await api.get('/audit/', { params })
  logs.value = data
}

onMounted(load)
</script>
