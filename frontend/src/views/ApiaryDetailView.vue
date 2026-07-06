<template>
  <div>
    <v-btn icon class="mb-2" @click="$router.back()"><v-icon>mdi-arrow-left</v-icon></v-btn>

    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2 class="text-truncate">{{ apiary?.name }}</h2>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNewHive" v-if="auth.hasRole('yard_manager')">
        Ajouter une ruche
      </v-btn>
    </div>

    <v-card class="mb-4 pa-4" v-if="apiary">
      <p v-if="apiary.address">📍 {{ apiary.address }}</p>
      <p v-if="apiary.description">{{ apiary.description }}</p>
    </v-card>

    <!-- Plan du rucher -->
    <v-card class="mb-4">
      <v-card-title>
        Plan du rucher <span class="text-caption text-grey ml-2">(glissez les ruches pour les placer)</span>
        <v-spacer />
        <v-btn v-if="canEdit" icon size="small" variant="text" @click="showPlanEditor = true" title="Fond du plan">
          <v-icon>mdi-pencil-ruler</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <div
          ref="planContainer"
          class="plan-container"
          :style="planBgImage ? { backgroundImage: 'url(' + planBgImage + ')', backgroundSize: 'cover', backgroundPosition: 'center' } : {}"
          @dragover.prevent
          @drop="onDrop"
        >
          <div
            v-for="hive in hives" :key="hive.id"
            class="hive-marker"
            :style="{ left: (hive.position_x != null ? hive.position_x : 20 + (hive.id * 60) % 500) + 'px', top: (hive.position_y != null ? hive.position_y : 50) + 'px' }"
            :class="{ 'hive-selected': selectedHive?.id === hive.id, 'hive-alert': hive.status === 'dead' }"
            :draggable="canEdit ? 'true' : 'false'"
            @dragstart="onDragStart($event, hive)"
            @click.stop="selectHive(hive)"
          >
            <div class="hive-diamond" :class="{ 'status-active': hive.status === 'active', 'status-dead': hive.status === 'dead', 'ownership-private': hive.ownership === 'private', 'ownership-associative': hive.ownership !== 'private' }">
              <div class="hive-number">{{ hive.napi_number || ('#' + hive.id) }}</div>
            </div>
            <div class="hive-fullname" :title="hive.name || hive.napi_number || ('Ruche #' + hive.id)">
              {{ hive.name || hive.napi_number || ('Ruche #' + hive.id) }}
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Panneau état de santé de la ruche sélectionnée -->
    <v-card v-if="selectedHive" class="mb-4" variant="outlined" color="primary">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-hexagon</v-icon>
        {{ selectedHive.name || selectedHive.napi_number || 'Ruche #' + selectedHive.id }}
        <v-chip :color="selectedHive.status === 'active' ? 'success' : 'error'" size="small" class="ml-2">
          {{ selectedHive.status }}
        </v-chip>
        <v-chip :color="selectedHive.ownership === 'private' ? 'orange' : 'blue'" size="x-small" class="ml-1">
          {{ selectedHive.ownership === 'private' ? '🏠 Privé' : '🏛️ Asso' }}
        </v-chip>
        <v-spacer />
        <v-btn size="small" variant="text" @click="selectedHive = null"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>
      <v-card-subtitle v-if="selectedHive.managers?.length" class="pb-0">
        <v-icon size="14" class="mr-1">mdi-account</v-icon>
        Responsable(s) : {{ selectedHive.managers.map(m => m.first_name ? m.first_name + ' ' + m.last_name : m.name).join(', ') }}
      </v-card-subtitle>
      <v-card-text>
        <div class="d-flex mb-3">
          <div v-if="selectedHive.photo_url" class="mr-3">
            <img :src="selectedHive.photo_url" alt="photo ruche" style="width:120px;height:80px;object-fit:cover;border-radius:6px;border:1px solid #ddd" />
          </div>
          <div>
            <v-file-input v-model="hivePhotoFile" accept="image/*" hide-details dense placeholder="Ajouter une photo" @change="uploadHivePhoto" />
            <v-btn v-if="selectedHive.photo_url" size="small" color="error" variant="text" @click="deleteHivePhoto(selectedHive.id)">Supprimer la photo</v-btn>
          </div>
        </div>
        <div v-if="lastVisitLoading" class="text-center pa-4">
          <v-progress-circular indeterminate size="24" />
        </div>
        <div v-else-if="lastVisit">
          <p class="text-caption text-grey mb-2">
            Dernière visite le {{ new Date(lastVisit.visited_at).toLocaleDateString('fr-FR') }}
            par {{ lastVisit.author_name }}
          </p>
          <v-row dense>
            <v-col cols="6" sm="3">
              <div class="text-center">
                <v-icon :color="lastVisit.queen_seen ? 'success' : lastVisit.queen_seen === false ? 'error' : 'grey'" size="28">
                  {{ lastVisit.queen_seen ? 'mdi-check-circle' : lastVisit.queen_seen === false ? 'mdi-close-circle' : 'mdi-help-circle' }}
                </v-icon>
                <div class="text-caption">Reine</div>
              </div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-center">
                <div class="text-h6" :class="broodColor(lastVisit.brood_score)">{{ lastVisit.brood_score != null ? lastVisit.brood_score + '/9' : 'N/A' }}</div>
                <div class="text-caption">Couvain</div>
              </div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-center">
                <div class="text-h6" :class="reservesColor(lastVisit.reserves_score)">{{ lastVisit.reserves_score != null ? lastVisit.reserves_score + '/9' : 'N/A' }}</div>
                <div class="text-caption">Réserves</div>
              </div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-center">
                <div class="text-h6">{{ lastVisit.supers_count != null ? lastVisit.supers_count : (lastVisit.supers_delta > 0 ? '+' : '') + lastVisit.supers_delta }}</div>
                <div class="text-caption">{{ lastVisit.supers_count != null ? 'Hausses' : 'Δ Hausses' }}</div>
              </div>
            </v-col>
          </v-row>
          <v-alert v-if="lastVisit.is_alert" type="error" density="compact" class="mt-2">
            🚨 {{ lastVisit.alert_message || 'Alerte signalée' }}
          </v-alert>
          <p v-if="lastVisit.feeding && lastVisit.feeding !== 'Aucun'" class="mt-2 text-body-2">
            🍯 Nourrissement : {{ lastVisit.feeding }}
          </p>
          <p v-if="lastVisit.honey_harvest_kg" class="mt-1 text-body-2">
            🏺 Récolte : {{ lastVisit.honey_harvest_kg }} kg
          </p>
          <v-card v-if="lastVisit.comment" variant="tonal" color="blue-grey" class="mt-2 pa-3">
            <div class="text-body-2"><v-icon size="16" class="mr-1">mdi-comment-text</v-icon>{{ lastVisit.comment }}</div>
          </v-card>
        </div>
        <div v-else class="text-center text-grey pa-2">
          Aucune visite enregistrée pour cette ruche
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn size="small" color="green-darken-2" variant="tonal" @click="openVisitDialog(selectedHive)">
          <v-icon class="mr-1">mdi-clipboard-check</v-icon> Visiter
        </v-btn>
        <v-btn size="small" color="primary" variant="text" @click="editHive(selectedHive)">
          <v-icon class="mr-1">mdi-pencil</v-icon> Modifier
        </v-btn>
        <v-spacer />
        <v-btn v-if="auth.isAdmin" size="small" color="error" variant="text" @click="deleteHive(selectedHive.id)">
          <v-icon class="mr-1">mdi-delete</v-icon> Supprimer
        </v-btn>
      </v-card-actions>

      <!-- Résumé sanitaire -->
      <v-card variant="outlined" class="ma-3 pa-3" v-if="sanitarySummary">
        <div class="text-subtitle-2 font-weight-bold mb-2">
          <v-icon class="mr-1" color="green-darken-2">mdi-shield-check</v-icon> Suivi sanitaire
        </div>
        <v-row dense>
          <v-col cols="12" sm="6" v-if="sanitarySummary.last_treatment">
            <div class="text-caption text-grey">Dernier traitement</div>
            <div class="text-body-2 font-weight-bold">{{ sanitarySummary.last_treatment.treatment_type }}</div>
            <div class="text-caption">{{ sanitarySummary.last_treatment.product }} · {{ new Date(sanitarySummary.last_treatment.date).toLocaleDateString('fr-FR') }}</div>
            <div class="text-caption" v-if="sanitarySummary.last_treatment.end_date">→ fin : {{ new Date(sanitarySummary.last_treatment.end_date).toLocaleDateString('fr-FR') }}</div>
          </v-col>
          <v-col cols="12" sm="6" v-if="sanitarySummary.last_varroa">
            <div class="text-caption text-grey">Dernier comptage varroa</div>
            <v-chip :color="sanitarySummary.last_varroa.varroa_count > 3 ? 'error' : sanitarySummary.last_varroa.varroa_count > 1 ? 'warning' : 'success'" size="small" class="mr-1">
              {{ sanitarySummary.last_varroa.varroa_count }} varroas/jour
            </v-chip>
            <span class="text-caption">{{ new Date(sanitarySummary.last_varroa.date).toLocaleDateString('fr-FR') }}</span>
          </v-col>
          <v-col cols="12" v-if="!sanitarySummary.last_treatment && !sanitarySummary.last_varroa">
            <div class="text-caption text-grey text-center">Aucun suivi sanitaire enregistré</div>
          </v-col>
        </v-row>
      </v-card>
    </v-card>

    <!-- Liste des ruches -->
    <v-data-table :headers="hiveHeaders" :items="hives" density="compact" @click:row="(_, { item }) => selectHive(item)">
      <template v-slot:item.ownership="{ item }">
        <v-chip :color="item.ownership === 'private' ? 'orange' : 'blue'" size="small">{{ item.ownership === 'private' ? 'Privée' : 'Asso' }}</v-chip>
      </template>
      <template v-slot:item.status="{ item }">
        <v-chip :color="item.status === 'active' ? 'success' : 'error'" size="small">{{ item.status }}</v-chip>
      </template>
      <template v-slot:item.managers="{ item }">
        <v-chip v-for="m in item.managers" :key="m.id" size="x-small" class="mr-1">{{ m.name }}</v-chip>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn icon size="small" @click.stop="editHive(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn v-if="auth.isAdmin" icon size="small" @click.stop="deleteHive(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Dialog ruche -->
    <v-dialog v-model="showHiveForm" max-width="500">
      <v-card>
        <v-card-title>{{ hiveEditId ? 'Modifier' : 'Nouvelle' }} ruche</v-card-title>
        <v-card-text>
          <v-text-field v-model="hiveForm.name" label="Nom" />
          <v-text-field v-model="hiveForm.napi_number" label="N° NAPI" />
          <v-btn-toggle v-model="hiveForm.ownership" mandatory class="mb-3 d-flex">
            <v-btn value="associative" color="blue" class="flex-grow-1">🏛️ Associatif</v-btn>
            <v-btn value="private" color="orange" class="flex-grow-1">🏠 Privé</v-btn>
          </v-btn-toggle>
          <v-select v-model="hiveForm.status" :items="['active', 'inactive', 'dead']" label="Statut" />
          <v-select v-model="hiveForm.manager_ids" :items="allUsers" item-title="label" item-value="id" label="Responsables" multiple chips />
          <v-textarea v-model="hiveForm.notes" label="Notes" rows="2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showHiveForm = false">Annuler</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveHive">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog visite rapide -->
    <v-dialog v-model="showVisitDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="green-darken-2">mdi-clipboard-check</v-icon>
          Visite — {{ visitHive?.name || visitHive?.napi_number || 'Ruche #' + visitHive?.id }}
        </v-card-title>
        <v-card-text>
          <!-- Hausses -->
          <v-card variant="outlined" class="mb-3 pa-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon class="mr-1" color="amber-darken-3">mdi-beehive-outline</v-icon> Hausses
            </div>
            <div class="d-flex align-center justify-center ga-3">
              <v-btn icon color="error" @click="visitForm.supers_count = Math.max(0, visitForm.supers_count - 1)"><v-icon>mdi-minus</v-icon></v-btn>
              <div class="text-h4 font-weight-bold mx-3">{{ visitForm.supers_count }}</div>
              <v-btn icon color="success" @click="visitForm.supers_count++"><v-icon>mdi-plus</v-icon></v-btn>
            </div>
          </v-card>
          <!-- Corps -->
          <v-card variant="outlined" class="mb-3 pa-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon class="mr-1" color="deep-orange">mdi-hexagon-multiple</v-icon> Corps
            </div>
            <v-switch v-model="visitBodyOpened" label="Corps ouvert" color="primary" hide-details density="compact" class="mb-2" />
            <div class="mb-2">
              <p class="text-overline mb-1">Reine</p>
              <v-btn-toggle v-model="visitForm.queen_seen" mandatory class="d-flex">
                <v-btn :value="true" color="success" class="flex-grow-1"><v-icon>mdi-check-bold</v-icon></v-btn>
                <v-btn :value="false" color="error" class="flex-grow-1"><v-icon>mdi-close-thick</v-icon></v-btn>
              </v-btn-toggle>
            </div>
            <template v-if="visitBodyOpened">
              <v-slider v-model="visitForm.brood_score" :min="0" :max="9" :step="1" label="Couvain" thumb-label color="amber" class="mb-1" />
              <v-slider v-model="visitForm.reserves_score" :min="0" :max="9" :step="1" label="Réserves" thumb-label color="deep-orange" />
            </template>
            <v-chip v-else color="grey" variant="tonal" class="mt-1">N/A — corps non ouvert</v-chip>
          </v-card>
          <v-select v-model="visitForm.feeding" :items="['Aucun','Sirop 50/50','Sirop 70/30','Candi','Pâte protéinée']" label="Nourrissement" density="compact" />
          <v-textarea v-model="visitForm.comment" label="Commentaire" rows="2" />
          <v-switch v-model="visitForm.is_alert" label="🚨 Alerte" color="error" hide-details />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showVisitDialog = false">Annuler</v-btn>
          <v-btn color="green-darken-2" :loading="visitSaving" @click="saveQuickVisit">
            <v-icon class="mr-1">mdi-check</v-icon> Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog plan editor -->
    <v-dialog v-model="showPlanEditor" max-width="500">
      <v-card>
        <v-card-title>Personnaliser le plan</v-card-title>
        <v-card-text>
          <p class="text-body-2 mb-3">Ajoutez une photo aérienne ou un schéma en fond du plan du rucher.</p>
          <v-file-input
            v-model="planImageFile"
            label="Image de fond"
            accept="image/*"
            prepend-icon="mdi-camera"
            show-size
          />
          <v-btn v-if="planBgImage" color="error" variant="text" size="small" @click="clearPlanBg" class="mt-1">
            <v-icon class="mr-1">mdi-delete</v-icon> Supprimer le fond
          </v-btn>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showPlanEditor = false">Annuler</v-btn>
          <v-btn color="primary" @click="applyPlanBg">Appliquer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="errorSnack" color="error" timeout="4000">{{ errorMsg }}</v-snackbar>
    <v-snackbar v-model="successSnack" color="success" timeout="2000">{{ successMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const props = defineProps({ id: [String, Number] })
const route = useRoute()
const auth = useAuthStore()
const apiaryId = props.id || route.params.id

const apiary = ref(null)
const hives = ref([])
const allUsers = ref([])
const selectedHive = ref(null)
const lastVisit = ref(null)
const lastVisitLoading = ref(false)
const sanitarySummary = ref(null)
const canEdit = computed(() => auth.isAdmin || auth.hasRole('yard_manager'))
const showHiveForm = ref(false)
const hiveEditId = ref(null)
const saving = ref(false)
const errorSnack = ref(false)
const errorMsg = ref('')
const successSnack = ref(false)
const successMsg = ref('')
const dragHive = ref(null)

// Visit dialog
const showVisitDialog = ref(false)
const visitHive = ref(null)
const visitSaving = ref(false)
const visitBodyOpened = ref(true)
const visitForm = ref({
  queen_seen: null, brood_score: 5, reserves_score: 5,
  supers_count: 0, feeding: 'Aucun', comment: '', is_alert: false,
})

// Plan editor
const showPlanEditor = ref(false)
const planImageFile = ref(null)
const planBgImage = ref(localStorage.getItem('planBg_' + (props.id || '')) || null)
const hiveForm = ref({ name: '', napi_number: '', ownership: 'associative', status: 'active', notes: '', manager_ids: [] })
const hivePhotoFile = ref(null)

const hiveHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'N° NAPI', key: 'napi_number' },
  { title: 'Type', key: 'ownership' },
  { title: 'Statut', key: 'status' },
  { title: 'Responsables', key: 'managers', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false },
]

function showError(msg) {
  errorMsg.value = msg
  errorSnack.value = true
}

function broodColor(score) {
  if (score == null) return ''
  if (score >= 7) return 'text-success'
  if (score >= 4) return 'text-warning'
  return 'text-error'
}

function reservesColor(score) {
  if (score == null) return ''
  if (score >= 7) return 'text-success'
  if (score >= 4) return 'text-warning'
  return 'text-error'
}

// Charger la dernière visite quand on sélectionne une ruche
async function selectHive(hive) {
  selectedHive.value = hive
  lastVisit.value = null
  sanitarySummary.value = null
  lastVisitLoading.value = true
  try {
    const [visitRes, sanitaryRes] = await Promise.all([
      api.get(`/apiaries/hives/${hive.id}/last-visit`).catch(() => ({ data: null })),
      api.get(`/sanitary/hive/${hive.id}/summary`).catch(() => ({ data: null })),
    ])
    lastVisit.value = visitRes.data
    sanitarySummary.value = sanitaryRes.data
  } finally {
    lastVisitLoading.value = false
  }
}

// Drag & drop sur le plan
function onDragStart(event, hive) {
  if (!canEdit.value) { event.preventDefault(); return }
  dragHive.value = hive
  event.dataTransfer.effectAllowed = 'move'
}

async function onDrop(event) {
  if (!dragHive.value) return
  const rect = event.currentTarget.getBoundingClientRect()
  const x = Math.max(0, event.clientX - rect.left - 18)
  const y = Math.max(0, event.clientY - rect.top - 18)
  try {
    await api.put(`/apiaries/hives/${dragHive.value.id}`, { position_x: x, position_y: y })
    dragHive.value.position_x = x
    dragHive.value.position_y = y
  } catch (e) {
    showError('Erreur lors du déplacement')
  }
  dragHive.value = null
}

async function load() {
  try {
    const [apRes, hivesRes] = await Promise.all([
      api.get(`/apiaries/`),
      api.get(`/apiaries/${apiaryId}/hives`),
    ])
    apiary.value = apRes.data.find((a) => a.id == apiaryId)
    hives.value = hivesRes.data
  } catch (e) {
    showError('Erreur de chargement du rucher')
    console.error('Apiary detail load error:', e)
  }

  try {
    const usersRes = await api.get('/users/')
    allUsers.value = usersRes.data.map((u) => ({ id: u.id, label: `${u.first_name} ${u.last_name}` }))
  } catch { /* non-admin */ }
}

function openNewHive() {
  hiveEditId.value = null
  hiveForm.value = { name: '', napi_number: '', ownership: 'associative', status: 'active', notes: '', manager_ids: [] }
  showHiveForm.value = true
}

function editHive(h) {
  hiveEditId.value = h.id
  hiveForm.value = {
    name: h.name || '',
    napi_number: h.napi_number || '',
    ownership: h.ownership || 'associative',
    status: h.status,
    notes: h.notes || '',
    manager_ids: (h.managers || []).map((m) => m.id),
  }
  showHiveForm.value = true
}

async function saveHive() {
  saving.value = true
  try {
    if (hiveEditId.value) {
      await api.put(`/apiaries/hives/${hiveEditId.value}`, hiveForm.value)
    } else {
      await api.post('/apiaries/hives', { ...hiveForm.value, apiary_id: parseInt(apiaryId) })
    }
    showHiveForm.value = false
    hiveEditId.value = null
    hiveForm.value = { name: '', napi_number: '', ownership: 'associative', status: 'active', notes: '', manager_ids: [] }
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors de l\'enregistrement')
  } finally {
    saving.value = false
  }
}

async function uploadHivePhoto() {
  if (!hivePhotoFile.value || !selectedHive.value) return
  const file = hivePhotoFile.value
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await api.post(`/apiaries/hives/${selectedHive.value.id}/photo`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    selectedHive.value.photo_url = res.data.photo_url
    successMsg.value = 'Photo enregistrée'
    successSnack.value = true
    hivePhotoFile.value = null
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur upload photo')
  }
}

async function deleteHivePhoto(hiveId) {
  if (!confirm('Supprimer la photo de cette ruche ?')) return
  try {
    await api.delete(`/apiaries/hives/${hiveId}/photo`)
    selectedHive.value.photo_url = null
    successMsg.value = 'Photo supprimée'
    successSnack.value = true
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur suppression photo')
  }
}

async function deleteHive(id) {
  if (!confirm('Supprimer cette ruche ?')) return
  try {
    await api.delete(`/apiaries/hives/${id}`)
    if (selectedHive.value?.id === id) selectedHive.value = null
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors de la suppression')
  }
}

// ─── Visite rapide ─────────────────────────────────────
function openVisitDialog(hive) {
  visitHive.value = hive
  visitForm.value = {
    queen_seen: null, brood_score: 5, reserves_score: 5,
    supers_count: 0, feeding: 'Aucun', comment: '', is_alert: false,
  }
  visitBodyOpened.value = true
  showVisitDialog.value = true
}

async function saveQuickVisit() {
  if (!visitHive.value) return
  visitSaving.value = true
  try {
    await api.post('/visits/', {
      hive_id: visitHive.value.id,
      visited_at: new Date().toISOString(),
      queen_seen: visitForm.value.queen_seen,
      brood_score: visitBodyOpened.value ? visitForm.value.brood_score : null,
      reserves_score: visitBodyOpened.value ? visitForm.value.reserves_score : null,
      supers_count: visitForm.value.supers_count,
      supers_delta: 0,
      feeding: visitForm.value.feeding === 'Aucun' ? null : visitForm.value.feeding,
      comment: visitForm.value.comment || null,
      is_alert: visitForm.value.is_alert,
      alert_message: visitForm.value.is_alert ? (visitForm.value.comment || 'Alerte terrain') : null,
      is_live_mode: false,
    })
    showVisitDialog.value = false
    successMsg.value = '✅ Visite enregistrée'
    successSnack.value = true
    // Recharger le détail de la ruche
    await selectHive(visitHive.value)
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors de l\'enregistrement')
  } finally {
    visitSaving.value = false
  }
}

// ─── Plan background ──────────────────────────────────
function applyPlanBg() {
  if (planImageFile.value) {
    const reader = new FileReader()
    reader.onload = (e) => {
      planBgImage.value = e.target.result
      localStorage.setItem('planBg_' + apiaryId, e.target.result)
      showPlanEditor.value = false
    }
    reader.readAsDataURL(planImageFile.value)
  }
}

function clearPlanBg() {
  planBgImage.value = null
  localStorage.removeItem('planBg_' + apiaryId)
  planImageFile.value = null
}

function showSuccess(msg) { successMsg.value = msg; successSnack.value = true }

onMounted(load)
</script>

<style scoped>
.plan-container {
  position: relative;
  width: 100%;
  height: 400px;
  background: linear-gradient(135deg, #f5f0e1 0%, #e8dcc8 100%);
  border-radius: 8px;
  overflow: hidden;
  border: 2px dashed #c5b89e;
}
.hive-marker {
  position: absolute;
  cursor: grab;
  text-align: center;
  padding: 2px;
  transition: transform 0.15s, box-shadow 0.15s;
  border-radius: 8px;
}
.hive-marker:hover {
  transform: scale(1.15);
  background: rgba(255, 193, 7, 0.15);
}
.hive-selected {
  transform: scale(1.2);
  background: rgba(25, 118, 210, 0.15);
  box-shadow: 0 0 0 2px #1976d2;
  border-radius: 8px;
}
.hive-alert { filter: grayscale(1); opacity: 0.6; }

.hive-diamond {
  width: 48px;
  height: 48px;
  transform: rotate(45deg);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  margin: 0 auto;
}
.hive-diamond.status-active { background: #ffca28; }
.hive-diamond.status-dead { background: #bdbdbd; }
.hive-diamond.ownership-associative { background: linear-gradient(180deg, #81d4fa, #29b6f6); }
.hive-diamond.ownership-private { background: linear-gradient(180deg, #ffd54f, #ffb300); }
.hive-number {
  transform: rotate(-45deg);
  font-weight: 700;
  color: #3e2723;
}
.hive-fullname {
  background: rgba(255,255,255,0.95);
  padding: 4px 8px;
  border-radius: 6px;
  margin-top: 6px;
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.85rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
</style>
