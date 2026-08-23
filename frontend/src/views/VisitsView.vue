<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Visites</h2>
      <v-chip color="info" variant="tonal" size="small">
        <v-icon start>mdi-information</v-icon>
        Saisie depuis le tableau de bord
      </v-chip>
    </div>

    <v-data-table :headers="headers" :items="visits" density="compact">
      <template v-slot:item.visited_at="{ item }">
        {{ new Date(item.visited_at).toLocaleString('fr-FR') }}
      </template>
      <template v-slot:item.hive_name="{ item }">
        {{ item.hive_name || ('Ruche #' + item.hive_id) }}
      </template>
      <template v-slot:item.treatment_type="{ item }">
        <v-chip v-if="item.treatment_type" size="x-small" variant="tonal" color="info"
          :title="item.treatment_product || ''">
          <v-icon start size="11">mdi-medical-bag</v-icon>{{ item.treatment_type }}
        </v-chip>
        <span v-else class="r-muted">—</span>
      </template>
      <template v-slot:item.queen_seen="{ item }">
        <v-icon v-if="item.queen_seen === true" color="success" size="18">mdi-check-circle</v-icon>
        <v-icon v-else-if="item.queen_seen === false" color="error" size="18">mdi-close-circle</v-icon>
        <span v-else class="r-muted">—</span>
      </template>
      <template v-slot:item.comment="{ item }">
        <span v-if="item.comment" class="comment-cell" :title="item.comment">{{ item.comment }}</span>
        <span v-else class="text-medium-emphasis">—</span>
      </template>
      <template v-slot:item.is_alert="{ item }">
        <v-icon v-if="item.is_alert" color="error">mdi-alert</v-icon>
      </template>
      <template v-slot:item.actions="{ item }" v-if="canEdit">
        <v-btn icon size="small" variant="text" @click="editVisit(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn v-if="auth.isAdmin" icon size="small" @click="deleteVisit(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Dialog modification visite -->
    <v-dialog v-model="showForm" max-width="600">
      <v-card>
        <v-card-title>Modifier la visite</v-card-title>
        <v-card-text>
          <!-- Section Hausses -->
          <v-card variant="outlined" class="mb-4 pa-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon class="mr-1" color="primary">mdi-beehive-outline</v-icon> Hausses
            </div>
            <v-btn-toggle v-model="form.supers_delta" mandatory class="mb-3">
              <v-btn :value="-1" color="error">-1 Hausse</v-btn>
              <v-btn :value="0">= Hausse</v-btn>
              <v-btn :value="1" color="success">+1 Hausse</v-btn>
            </v-btn-toggle>
            <v-row dense>
              <v-col cols="6"><v-text-field v-model.number="form.honey_harvest_kg" label="Récolte miel (kg)" type="number" density="compact" /></v-col>
              <v-col cols="6"><v-text-field v-model.number="form.pollen_harvest_kg" label="Récolte pollen (kg)" type="number" density="compact" /></v-col>
            </v-row>
          </v-card>

          <!-- Section Corps -->
          <v-card variant="outlined" class="mb-4 pa-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon class="mr-1" color="accent">mdi-hexagon-multiple</v-icon> Corps
            </div>
            <v-switch v-model="form.queen_seen" label="Reine vue" color="success" />
            <v-slider v-model="form.brood_score" :min="0" :max="9" :step="1" label="Couvain" thumb-label />
            <v-slider v-model="form.reserves_score" :min="0" :max="9" :step="1" label="Réserves" thumb-label />
            <v-text-field v-model="form.feeding" label="Nourrissement" density="compact" />
            <!-- Traitement : saisi sur le terrain, il doit être consultable
                 et corrigeable depuis l'historique. -->
            <v-select
              v-model="form.treatment_type" :items="treatmentTypes"
              label="Type de traitement" placeholder="Aucun" clearable density="compact"
            />
            <v-combobox
              v-if="form.treatment_type"
              v-model="form.treatment_product" :items="productSuggestions"
              label="Produit utilisé" density="compact"
            />
          </v-card>

          <v-textarea v-model="form.comment" label="Commentaires" rows="2" />
          <v-switch v-model="form.is_alert" label="Alerte" color="error" />
          <v-text-field v-if="form.is_alert" v-model="form.alert_message" label="Message d'alerte" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showForm = false">Annuler</v-btn>
          <v-btn color="primary" @click="saveVisit">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { toastError, toastSuccess, apiError } from '../services/toast'
import { confirmAction } from '../services/confirm'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const canEdit = computed(() => auth.isAdmin || auth.hasRole('yard_manager'))
const visits = ref([])
const showForm = ref(false)
const formEditId = ref(null)
const form = ref({
  hive_id: null, queen_seen: null, brood_score: 5, reserves_score: 5,
  supers_delta: 0, feeding: '', comment: '', is_alert: false, alert_message: '', honey_harvest_kg: null, pollen_harvest_kg: null,
})

// Mêmes listes que la saisie terrain, pour que les libellés concordent.
const treatmentTypes = [
  'Varroa', 'Loque américaine', 'Loque européenne',
  'Nosémose', 'Teigne', 'Frelon asiatique', 'Autre',
]
const productSuggestions = [
  'Apivar', 'Apiguard', 'Apilife Var', 'VarroMed',
  'Acide oxalique (dégouttement)', 'Acide oxalique (sublimation)',
  'Acide formique (MAQS)', 'Thymol',
]

const headers = computed(() => {
  const h = [
    { title: 'Date', key: 'visited_at' },
    { title: 'Ruche', key: 'hive_name' },
    { title: 'Auteur', key: 'author_name' },
    { title: 'Reine', key: 'queen_seen' },
    { title: 'Couvain', key: 'brood_score' },
    { title: 'Réserves', key: 'reserves_score' },
    { title: 'Hausses', key: 'supers_delta' },
    { title: 'Traitement', key: 'treatment_type' },
    { title: 'Commentaire', key: 'comment', sortable: false },
    { title: 'Alerte', key: 'is_alert' },
  ]
  if (canEdit.value) h.push({ title: 'Actions', key: 'actions', sortable: false })
  return h
})

async function load() {
  try {
    const { data } = await api.get('/visits/?limit=100')
    visits.value = data
  } catch (e) {
    toastError(apiError(e, 'Chargement des visites impossible'))
  }
}

function editVisit(v) {
  formEditId.value = v.id
  form.value = {
    queen_seen: v.queen_seen,
    brood_score: v.brood_score,
    reserves_score: v.reserves_score,
    supers_delta: v.supers_delta,
    feeding: v.feeding || '',
    comment: v.comment || '',
    is_alert: v.is_alert,
    alert_message: v.alert_message || '',
    honey_harvest_kg: v.honey_harvest_kg,
    pollen_harvest_kg: v.pollen_harvest_kg,
    treatment_type: v.treatment_type || null,
    treatment_product: v.treatment_product || null,
  }
  showForm.value = true
}

async function saveVisit() {
  try {
    await api.put(`/visits/${formEditId.value}`, form.value)
    showForm.value = false
    formEditId.value = null
    await load()
    toastSuccess('Visite modifiée')
  } catch (e) {
    toastError(apiError(e, "Erreur lors de l'enregistrement"))
  }
}

async function deleteVisit(id) {
  if (!(await confirmAction('Supprimer cette visite ?'))) return
  try {
    await api.delete(`/visits/${id}`)
    await load()
    toastSuccess('Visite supprimée')
  } catch (e) {
    toastError(apiError(e, 'Erreur lors de la suppression'))
  }
}

onMounted(load)
</script>

<style scoped>
.comment-cell {
  display: inline-block;
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: bottom;
  cursor: help;
}
</style>
