<template>
  <div>
    <v-btn icon class="mb-2" @click="$router.back()"><v-icon>mdi-arrow-left</v-icon></v-btn>

    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2 class="text-truncate">{{ apiary?.name }}</h2>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNewHive" v-if="auth.hasRole('yard_manager')">
        Ajouter une ruche
      </v-btn>
    </div>

    <v-card class="mb-4" v-if="apiary">
      <v-card-text>
        <p v-if="apiary.address" class="mb-1"><v-icon size="15" class="mr-1">mdi-map-marker</v-icon>{{ apiary.address }}</p>
        <p v-if="apiary.description" class="mb-0">{{ apiary.description }}</p>
        <div v-if="canEdit" class="d-flex flex-wrap align-center ga-2 mt-3">
          <v-file-input v-model="apiaryPhotoFile" accept="image/*" density="compact" hide-details
            prepend-icon="mdi-camera" :label="apiary.photo_url ? 'Remplacer la photo aérienne' : 'Ajouter une photo aérienne'"
            style="max-width:340px" :loading="photoUploading" @update:model-value="uploadApiaryPhoto" />
          <v-btn v-if="apiary.photo_url" size="small" color="error" variant="text" @click="deleteApiaryPhoto">
            Supprimer la photo
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Plan du rucher -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        Plan du rucher
        <v-spacer />
        <v-btn v-if="canEdit && apiary?.photo_url" size="small" variant="tonal" prepend-icon="mdi-crop" @click="showCrop = true">
          Recadrer
        </v-btn>
      </v-card-title>
      <v-card-text>
        <ApiaryPlan
          :photo-url="apiary?.photo_url"
          :hives="hives"
          :can-edit="canEdit"
          :selected-id="selectedHive?.id"
          @select="selectHive"
          @move="onMarkerMove"
        />
        <p v-if="!apiary?.photo_url" class="text-caption text-medium-emphasis mt-2">
          Ajoutez une photo aérienne (ci-dessus) : elle servira de fond au plan.
        </p>
      </v-card-text>
    </v-card>

    <!-- Panneau état de santé de la ruche sélectionnée -->
    <v-card v-if="selectedHive" class="mb-4" variant="outlined" color="primary">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-hexagon</v-icon>
        {{ selectedHive.name || selectedHive.number || selectedHive.napi_number || 'Ruche #' + selectedHive.id }}
        <v-chip :color="selectedHive.status === 'active' ? 'success' : 'error'" size="small" class="ml-2">
          {{ selectedHive.status }}
        </v-chip>
        <v-chip :color="selectedHive.ownership === 'private' ? 'orange' : 'blue'" size="x-small" class="ml-1">
          {{ selectedHive.ownership === 'private' ? 'Privée' : 'Associative' }}
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
          <p class="text-caption r-muted mb-2">
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
          <v-card v-if="lastVisit.comment" variant="tonal" color="secondary" class="mt-2 pa-3">
            <div class="text-body-2"><v-icon size="16" class="mr-1">mdi-comment-text</v-icon>{{ lastVisit.comment }}</div>
          </v-card>
        </div>
        <div v-else class="text-center r-muted pa-2">
          Aucune visite enregistrée pour cette ruche
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn size="small" color="green-darken-2" variant="tonal" @click="openVisitDialog(selectedHive)">
          <v-icon class="mr-1">mdi-clipboard-check</v-icon> Visiter
        </v-btn>
        <v-btn size="small" color="info" variant="text" prepend-icon="mdi-swap-horizontal"
          @click="openMoveHive(selectedHive)">
          Déplacer
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
            <div class="text-caption r-muted">Dernier traitement</div>
            <div class="text-body-2 font-weight-bold">{{ sanitarySummary.last_treatment.treatment_type }}</div>
            <div class="text-caption">{{ sanitarySummary.last_treatment.product }} · {{ new Date(sanitarySummary.last_treatment.date).toLocaleDateString('fr-FR') }}</div>
            <div class="text-caption" v-if="sanitarySummary.last_treatment.end_date">→ fin : {{ new Date(sanitarySummary.last_treatment.end_date).toLocaleDateString('fr-FR') }}</div>
          </v-col>
          <v-col cols="12" sm="6" v-if="sanitarySummary.last_varroa">
            <div class="text-caption r-muted">Dernier comptage varroa</div>
            <v-chip :color="sanitarySummary.last_varroa.varroa_count > 3 ? 'error' : sanitarySummary.last_varroa.varroa_count > 1 ? 'warning' : 'success'" size="small" class="mr-1">
              {{ sanitarySummary.last_varroa.varroa_count }} varroas/jour
            </v-chip>
            <span class="text-caption">{{ new Date(sanitarySummary.last_varroa.date).toLocaleDateString('fr-FR') }}</span>
          </v-col>
          <v-col cols="12" v-if="!sanitarySummary.last_treatment && !sanitarySummary.last_varroa">
            <div class="text-caption r-muted text-center">Aucun suivi sanitaire enregistré</div>
          </v-col>
        </v-row>
      </v-card>
    </v-card>

    <!-- Liste des ruches -->
    <v-data-table :headers="hiveHeaders" :items="hives" density="compact" @click:row="(_, { item }) => selectHive(item)">
      <template v-slot:item.ownership="{ item }">
        <v-chip :color="item.ownership === 'private' ? 'accent' : 'info'" size="small" variant="tonal">{{ item.ownership === 'private' ? 'Privée' : 'Associative' }}</v-chip>
      </template>
      <template v-slot:item.status="{ item }">
        <v-chip :color="item.status === 'active' ? 'success' : 'error'" size="small">{{ item.status }}</v-chip>
      </template>
      <template v-slot:item.managers="{ item }">
        <v-chip v-for="m in item.managers" :key="m.id" size="x-small" class="mr-1">{{ m.name }}</v-chip>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn icon size="small" variant="text" title="Modifier" @click.stop="editHive(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn icon size="small" variant="text" title="Déplacer vers un autre rucher" @click.stop="openMoveHive(item)">
          <v-icon color="info">mdi-swap-horizontal</v-icon>
        </v-btn>
        <v-btn v-if="auth.isAdmin" icon size="small" @click.stop="deleteHive(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Dialog ruche -->
    <v-dialog v-model="showHiveForm" max-width="500">
      <v-card>
        <v-card-title>{{ hiveEditId ? 'Modifier' : 'Nouvelle' }} ruche</v-card-title>
        <v-card-text>
          <v-text-field v-model="hiveForm.name" label="Nom" />
          <v-text-field
            v-model="hiveForm.number"
            label="N° de ruche"
            prepend-inner-icon="mdi-pound"
            hint="Numéro propre à cette ruche : deux ruches ne peuvent pas le partager."
            persistent-hint
            :error-messages="numberError"
            class="mb-2"
          />
          <v-text-field
            v-model="hiveForm.napi_number"
            label="N° NAPI (apiculteur)"
            prepend-inner-icon="mdi-card-account-details-outline"
            hint="Numéro d'apiculteur du propriétaire — le même pour toutes ses ruches."
            persistent-hint
            class="mb-2"
          />
          <v-btn-toggle v-model="hiveForm.ownership" mandatory class="mb-3 d-flex">
            <v-btn value="associative" color="info" class="flex-grow-1" prepend-icon="mdi-account-group">Associatif</v-btn>
            <v-btn value="private" color="accent" class="flex-grow-1" prepend-icon="mdi-home">Privé</v-btn>
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

    <!-- Dialog déplacement de ruche -->
    <v-dialog v-model="showMoveHive" max-width="480">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="info">mdi-swap-horizontal</v-icon>
          Déplacer la ruche
        </v-card-title>
        <v-card-text>
          <p class="text-body-2 r-muted mb-4">
            Transhumance ou réorganisation : la ruche change de rucher et
            emporte tout son historique — visites, traitements, récoltes.
          </p>
          <v-alert v-if="moveHiveTarget" density="compact" variant="tonal" class="mb-4">
            <b>{{ moveHiveTarget.name || moveHiveTarget.number || moveHiveTarget.napi_number || 'Ruche #' + moveHiveTarget.id }}</b>
            <div class="text-caption">Actuellement au rucher « {{ apiary?.name }} »</div>
          </v-alert>
          <v-select
            v-model="moveApiaryId"
            :items="otherApiaries"
            item-title="name" item-value="id"
            label="Rucher de destination"
            prepend-inner-icon="mdi-hexagon-multiple"
            :error-messages="moveError"
            :no-data-text="'Aucun autre rucher enregistré'"
          />
          <v-alert type="info" variant="tonal" density="compact">
            <v-icon start size="15">mdi-map-marker-off-outline</v-icon>
            Sa position sur le plan sera effacée : elle désignait un emplacement
            sur la photo de ce rucher-ci. Replacez-la sur le nouveau plan.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showMoveHive = false">Annuler</v-btn>
          <v-btn color="info" :loading="saving" :disabled="!otherApiaries.length" @click="confirmMoveHive">
            Déplacer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog visite rapide -->
    <v-dialog v-model="showVisitDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="green-darken-2">mdi-clipboard-check</v-icon>
          Visite — {{ visitHive?.name || visitHive?.number || visitHive?.napi_number || 'Ruche #' + visitHive?.id }}
        </v-card-title>
        <v-card-text>
          <!-- Hausses -->
          <v-card variant="outlined" class="mb-3 pa-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon class="mr-1" color="primary">mdi-beehive-outline</v-icon> Hausses
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
              <v-icon class="mr-1" color="accent">mdi-hexagon-multiple</v-icon> Corps
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
              <v-slider v-model="visitForm.brood_score" :min="0" :max="9" :step="1" label="Couvain" thumb-label color="primary" class="mb-1" />
              <v-slider v-model="visitForm.reserves_score" :min="0" :max="9" :step="1" label="Réserves" thumb-label color="accent" />
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

    <!-- Recadrage de la photo (admin) -->
    <PhotoFrameDialog v-model="showCrop" :src="apiary?.photo_url" @cropped="onCropped" />

    <v-snackbar v-model="errorSnack" color="error" timeout="4000">{{ errorMsg }}</v-snackbar>
    <v-snackbar v-model="successSnack" color="success" timeout="2000">{{ successMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { apiError } from '../services/toast'
import { useRoute } from 'vue-router'
import api from '../services/api'
import { confirmAction } from '../services/confirm'
import { useAuthStore } from '../stores/auth'
import ApiaryPlan from '../components/ApiaryPlan.vue'
import PhotoFrameDialog from '../components/PhotoFrameDialog.vue'

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
// Message d'unicité du numéro de ruche, affiché sous le champ concerné plutôt
// qu'en bandeau : c'est là qu'il faut corriger.
const numberError = ref('')

// ─── Déplacement d'une ruche vers un autre rucher ─────────
const showMoveHive = ref(false)
const moveHiveTarget = ref(null)
const moveApiaryId = ref(null)
const moveError = ref('')
const allApiaries = ref([])
const otherApiaries = computed(
  () => allApiaries.value.filter((a) => a.id !== Number(apiaryId)),
)
// Le reproche disparaît dès qu'on y répond.
watch(moveApiaryId, (v) => { if (v) moveError.value = '' })
const hiveEditId = ref(null)
const saving = ref(false)
const errorSnack = ref(false)
const errorMsg = ref('')
const successSnack = ref(false)
const successMsg = ref('')

// Visit dialog
const showVisitDialog = ref(false)
const visitHive = ref(null)
const visitSaving = ref(false)
const visitBodyOpened = ref(true)
const visitForm = ref({
  queen_seen: null, brood_score: 5, reserves_score: 5,
  supers_count: 0, feeding: 'Aucun', comment: '', is_alert: false,
})

// Recadrage photo (admin)
const showCrop = ref(false)
const hiveForm = ref({ name: '', number: '', napi_number: '', ownership: 'associative', status: 'active', notes: '', manager_ids: [] })
// Corriger la saisie retire le reproche.
watch(() => hiveForm.value.number, () => { numberError.value = '' })
const hivePhotoFile = ref(null)
const apiaryPhotoFile = ref(null)
const photoUploading = ref(false)

const hiveHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'N° ruche', key: 'number' },
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

// Déplacement d'une ruche sur le plan (positions en %, stables sur tout écran)
async function onMarkerMove({ id, x, y }) {
  try {
    await api.put(`/apiaries/hives/${id}`, { position_x: x, position_y: y })
    const h = hives.value.find((v) => v.id === id)
    if (h) { h.position_x = x; h.position_y = y }
  } catch (e) {
    showError(apiError(e, 'Déplacement impossible'))
  }
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
    showError(apiError(e, 'Chargement du rucher impossible'))
    console.error('Apiary detail load error:', e)
  }

  try {
    const usersRes = await api.get('/users/')
    allUsers.value = usersRes.data.map((u) => ({ id: u.id, label: `${u.first_name} ${u.last_name}` }))
  } catch { /* non-admin */ }
}

function openMoveHive(h) {
  moveHiveTarget.value = h
  moveApiaryId.value = null
  moveError.value = ''
  showMoveHive.value = true
  if (!allApiaries.value.length) loadApiaries()
}

async function loadApiaries() {
  try {
    const { data } = await api.get('/apiaries/')
    allApiaries.value = data
  } catch (e) {
    showError(apiError(e, 'Impossible de charger la liste des ruchers'))
  }
}

async function confirmMoveHive() {
  if (!moveApiaryId.value) { moveError.value = 'Choisissez le rucher de destination.'; return }
  saving.value = true
  try {
    const { data } = await api.post(
      `/apiaries/hives/${moveHiveTarget.value.id}/move`,
      { apiary_id: moveApiaryId.value },
    )
    showMoveHive.value = false
    showSuccess(`Ruche déplacée vers « ${data.apiary_name} »`)
    // La ruche ne fait plus partie de ce rucher : on referme son panneau.
    if (selectedHive.value?.id === moveHiveTarget.value.id) selectedHive.value = null
    await load()
  } catch (e) {
    moveError.value = apiError(e, 'Déplacement impossible')
  } finally {
    saving.value = false
  }
}

function openNewHive() {
  hiveEditId.value = null
  numberError.value = ''
  hiveForm.value = { name: '', number: '', napi_number: '', ownership: 'associative', status: 'active', notes: '', manager_ids: [] }
  showHiveForm.value = true
}

function editHive(h) {
  hiveEditId.value = h.id
  numberError.value = ''
  hiveForm.value = {
    name: h.name || '',
    number: h.number || '',
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
  numberError.value = ''
  try {
    if (hiveEditId.value) {
      await api.put(`/apiaries/hives/${hiveEditId.value}`, hiveForm.value)
    } else {
      await api.post('/apiaries/hives', { ...hiveForm.value, apiary_id: parseInt(apiaryId) })
    }
    showHiveForm.value = false
    hiveEditId.value = null
    hiveForm.value = { name: '', number: '', napi_number: '', ownership: 'associative', status: 'active', notes: '', manager_ids: [] }
    await load()
  } catch (e) {
    const msg = apiError(e, "Enregistrement impossible")
    // Numéro déjà pris : le message appartient au champ, pas au bandeau —
    // sinon on ne sait pas quoi corriger.
    if (e?.response?.status === 409) numberError.value = msg
    else showError(msg)
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
    showError(apiError(e, 'Erreur upload photo'))
  }
}

async function deleteHivePhoto(hiveId) {
  if (!(await confirmAction('Supprimer la photo de cette ruche ?'))) return
  try {
    await api.delete(`/apiaries/hives/${hiveId}/photo`)
    selectedHive.value.photo_url = null
    successMsg.value = 'Photo supprimée'
    successSnack.value = true
    await load()
  } catch (e) {
    showError(apiError(e, 'Erreur suppression photo'))
  }
}

// ─── Photo aérienne du rucher ──────────────────────────
// Redimensionne/compresse côté client pour un chargement rapide.
function compressImage(file, maxDim = 1600, quality = 0.82) {
  return new Promise((resolve) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      let { width, height } = img
      if (Math.max(width, height) > maxDim) {
        const r = maxDim / Math.max(width, height)
        width = Math.round(width * r); height = Math.round(height * r)
      }
      const canvas = document.createElement('canvas')
      canvas.width = width; canvas.height = height
      canvas.getContext('2d').drawImage(img, 0, 0, width, height)
      canvas.toBlob((blob) => resolve(blob || file), 'image/jpeg', quality)
    }
    img.onerror = () => { URL.revokeObjectURL(url); resolve(file) }
    img.src = url
  })
}

async function sendApiaryPhoto(blob) {
  photoUploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', blob, 'rucher.jpg')
    const res = await api.post(`/apiaries/${apiaryId}/photo`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (apiary.value) apiary.value.photo_url = res.data.photo_url
    showSuccess('Photo du rucher enregistrée')
    await load()
  } catch (e) {
    showError(apiError(e, 'Erreur upload photo'))
  } finally {
    photoUploading.value = false
  }
}

async function uploadApiaryPhoto() {
  if (!apiaryPhotoFile.value) return
  const file = Array.isArray(apiaryPhotoFile.value) ? apiaryPhotoFile.value[0] : apiaryPhotoFile.value
  if (!file) return
  const blob = await compressImage(file)
  apiaryPhotoFile.value = null
  await sendApiaryPhoto(blob)
}

// Recadrage (admin) : le composant renvoie l'image rognée, on la ré-enregistre.
async function onCropped(blob) {
  if (blob) await sendApiaryPhoto(blob)
}

async function deleteApiaryPhoto() {
  if (!(await confirmAction('Supprimer la photo du rucher ?'))) return
  try {
    await api.delete(`/apiaries/${apiaryId}/photo`)
    if (apiary.value) apiary.value.photo_url = null
    showSuccess('Photo supprimée')
    await load()
  } catch (e) {
    showError(apiError(e, 'Erreur suppression photo'))
  }
}

async function deleteHive(id) {
  if (!(await confirmAction('Supprimer cette ruche ?'))) return
  try {
    await api.delete(`/apiaries/hives/${id}`)
    if (selectedHive.value?.id === id) selectedHive.value = null
    await load()
  } catch (e) {
    showError(apiError(e, 'Erreur lors de la suppression'))
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
    successMsg.value = 'Visite enregistrée'
    successSnack.value = true
    // Recharger le détail de la ruche
    await selectHive(visitHive.value)
  } catch (e) {
    showError(apiError(e, 'Erreur lors de l\'enregistrement'))
  } finally {
    visitSaving.value = false
  }
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
