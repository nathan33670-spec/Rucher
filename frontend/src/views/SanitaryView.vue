<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Suivi sanitaire</h2>
      <div class="d-flex flex-wrap ga-2">
        <v-btn v-if="canEdit" color="primary" prepend-icon="mdi-needle" @click="openTreatment">
          Traitement
        </v-btn>
        <v-btn color="secondary" variant="tonal" prepend-icon="mdi-bug" @click="openVarroa">
          Comptage Varroa
        </v-btn>
      </div>
    </div>

    <!-- Onglets -->
    <v-tabs v-model="activeTab" class="mb-4" color="primary">
      <v-tab value="treatments" prepend-icon="mdi-needle">Traitements</v-tab>
      <v-tab value="varroa" prepend-icon="mdi-bug-outline">Comptages</v-tab>
    </v-tabs>

    <FilterBar
      v-model="filters" :fields="filterFields"
      :total="currentRows.length" :shown="filteredRows.length"
      :item-label="activeTab === 'treatments' ? 'traitement' : 'comptage'"
    />

    <!-- Tableau traitements -->
    <v-data-table v-if="activeTab === 'treatments'" :headers="treatmentHeaders" :items="filteredRows" density="compact">
      <template v-slot:item.application_date="{ item }">
        {{ new Date(item.application_date).toLocaleDateString('fr-FR') }}
      </template>
      <template v-slot:item.end_date="{ item }">
        {{ item.end_date ? new Date(item.end_date).toLocaleDateString('fr-FR') : '—' }}
      </template>
      <template v-slot:item.hive_name="{ item }">
        <v-chip size="small" color="primary" variant="tonal">{{ item.hive_name || '#' + item.hive_id }}</v-chip>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn v-if="canEdit" icon size="small" variant="text" @click="editRecord(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn v-if="auth.isAdmin" icon size="small" variant="text" @click="deleteRecord(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Tableau varroa -->
    <v-data-table v-if="activeTab === 'varroa'" :headers="varroaHeaders" :items="filteredRows" density="compact">
      <template v-slot:item.application_date="{ item }">
        {{ new Date(item.application_date).toLocaleDateString('fr-FR') }}
      </template>
      <template v-slot:item.hive_name="{ item }">
        <v-chip size="small" color="primary" variant="tonal">{{ item.hive_name || '#' + item.hive_id }}</v-chip>
      </template>
      <template v-slot:item.varroa_count="{ item }">
        <v-chip :color="item.varroa_count > 3 ? 'error' : item.varroa_count > 1 ? 'warning' : 'success'" size="small">
          {{ item.varroa_count }} varroas/jour
        </v-chip>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn v-if="canEdit" icon size="small" variant="text" @click="editRecord(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn v-if="auth.isAdmin" icon size="small" variant="text" @click="deleteRecord(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Dialog traitement -->
    <v-dialog v-model="showTreatmentForm" max-width="600">
      <v-card>
        <v-card-title>{{ editId ? 'Modifier le' : 'Nouveau' }} traitement</v-card-title>
        <v-card-text>
          <v-select
            v-if="!editId"
            v-model="form.hive_ids"
            :items="hiveOptions"
            item-title="label"
            item-value="id"
            label="Ruches concernées"
            multiple
            chips
            closable-chips
          >
            <template v-slot:prepend-item>
              <v-list-item title="Toutes les ruches" @click="toggleAll">
                <template v-slot:prepend>
                  <v-checkbox-btn :model-value="allSelected" :indeterminate="someSelected && !allSelected" />
                </template>
              </v-list-item>
              <v-divider />
            </template>
          </v-select>
          <v-text-field v-model="form.treatment_type" label="Type de traitement" placeholder="ex: Anti-varroa, Nourrissement stimulant..." />
          <v-text-field v-model="form.product" label="Produit" placeholder="ex: Apivar, Acide oxalique..." />
          <v-text-field v-model="form.dosage" label="Dosage" placeholder="ex: 2 lanières, 3.5% en dégouttement..." />
          <v-row>
            <v-col><v-text-field v-model="form.application_date" label="Date de début" type="date" /></v-col>
            <v-col><v-text-field v-model="form.end_date" label="Date de fin" type="date" /></v-col>
          </v-row>
          <v-textarea v-model="form.notes" label="Notes" rows="2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showTreatmentForm = false">Annuler</v-btn>
          <v-btn color="green-darken-2" :loading="saving" @click="saveTreatment">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog comptage varroa -->
    <v-dialog v-model="showVarroaForm" max-width="500">
      <v-card>
        <v-card-title>{{ editId ? 'Modifier le' : 'Nouveau' }} comptage Varroa</v-card-title>
        <v-card-text>
          <v-select
            v-if="!editId"
            v-model="form.hive_ids"
            :items="hiveOptions"
            item-title="label"
            item-value="id"
            label="Ruches concernées"
            multiple
            chips
            closable-chips
          />
          <v-text-field v-model="form.application_date" label="Date du comptage" type="date" />
          <v-text-field v-model.number="form.varroa_count" label="Nombre de varroas / jour" type="number" min="0" />
          <v-textarea v-model="form.notes" label="Notes / Méthode" rows="2" placeholder="ex: Lange graissé 3 jours, lavage alcool..." />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showVarroaForm = false">Annuler</v-btn>
          <v-btn color="red-darken-2" :loading="saving" @click="saveVarroa">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="successSnack" color="success" timeout="2000">{{ successMsg }}</v-snackbar>
    <v-snackbar v-model="errorSnack" color="error" timeout="4000">{{ errorMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FilterBar from '../components/FilterBar.vue'
import { apiError } from '../services/toast'
import api from '../services/api'
import { confirmAction } from '../services/confirm'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const canEdit = computed(() => auth.isAdmin || auth.hasRole('yard_manager'))

const activeTab = ref('treatments')
const treatments = ref([])
const varroaCounts = ref([])

// ─── Filtres ──────────────────────────────────────────────
// Le registre sanitaire se consulte ruche par ruche : c'est la question qu'on
// se pose devant une colonie, pas « toutes les ruches par date ».
const filters = ref({ hive: null, kind: null, from: null, to: null })
const currentRows = computed(() => (activeTab.value === 'treatments' ? treatments.value : varroaCounts.value))
const rowHive = (r) => r.hive_name || ('Ruche #' + r.hive_id)
const uniq = (l) => [...new Set(l.filter(Boolean))].sort((a, b) => a.localeCompare(b))

const filterFields = computed(() => {
  const f = [
    { key: 'hive', label: 'Ruche', type: 'select', icon: 'mdi-beehive-outline',
      items: uniq(currentRows.value.map(rowHive)).map((n) => ({ title: n, value: n })) },
  ]
  if (activeTab.value === 'treatments') {
    f.push({ key: 'kind', label: 'Type de traitement', type: 'select', icon: 'mdi-medical-bag',
      items: uniq(treatments.value.map((r) => r.treatment_type)).map((n) => ({ title: n, value: n })) })
  }
  f.push({ key: 'from', label: 'Du', type: 'date' })
  f.push({ key: 'to', label: 'Au', type: 'date' })
  return f
})

const filteredRows = computed(() => {
  const f = filters.value
  return currentRows.value.filter((r) => {
    if (f.hive && rowHive(r) !== f.hive) return false
    if (f.kind && r.treatment_type !== f.kind) return false
    const d = (r.application_date || '').substring(0, 10)
    if (f.from && d < f.from) return false
    if (f.to && d > f.to) return false
    return true
  })
})
const hiveOptions = ref([])

const showTreatmentForm = ref(false)
const showVarroaForm = ref(false)
const editId = ref(null)
const saving = ref(false)
const successSnack = ref(false)
const successMsg = ref('')
const errorSnack = ref(false)
const errorMsg = ref('')

const defaultForm = {
  hive_ids: [], hive_id: null, record_type: 'treatment',
  treatment_type: '', product: '', dosage: '',
  application_date: new Date().toISOString().slice(0, 10), end_date: null,
  varroa_count: null, notes: '',
}
const form = ref({ ...defaultForm })

const treatmentHeaders = [
  { title: 'Ruche', key: 'hive_name' },
  { title: 'Traitement', key: 'treatment_type' },
  { title: 'Produit', key: 'product' },
  { title: 'Dosage', key: 'dosage' },
  { title: 'Début', key: 'application_date' },
  { title: 'Fin', key: 'end_date' },
  { title: 'Actions', key: 'actions', sortable: false },
]

const varroaHeaders = [
  { title: 'Ruche', key: 'hive_name' },
  { title: 'Date', key: 'application_date' },
  { title: 'Varroas/jour', key: 'varroa_count' },
  { title: 'Notes', key: 'notes' },
  { title: 'Actions', key: 'actions', sortable: false },
]

const allSelected = computed(() => hiveOptions.value.length > 0 && form.value.hive_ids.length === hiveOptions.value.length)
const someSelected = computed(() => form.value.hive_ids.length > 0)

function toggleAll() {
  if (allSelected.value) {
    form.value.hive_ids = []
  } else {
    form.value.hive_ids = hiveOptions.value.map(h => h.id)
  }
}

function showError(msg) { errorMsg.value = msg; errorSnack.value = true }
function showSuccess(msg) { successMsg.value = msg; successSnack.value = true }

async function load() {
  try {
    const [tRes, vRes, aRes] = await Promise.all([
      api.get('/sanitary/', { params: { record_type: 'treatment' } }),
      api.get('/sanitary/', { params: { record_type: 'varroa_count' } }),
      api.get('/apiaries/'),
    ])
    treatments.value = tRes.data
    varroaCounts.value = vRes.data
    const opts = []
    for (const ap of aRes.data) {
      try {
        const { data: hives } = await api.get('/apiaries/' + ap.id + '/hives')
        for (const h of hives) {
          if (h.status === 'active') opts.push({ id: h.id, label: ap.name + ' — ' + (h.name || '#' + h.id) })
        }
      } catch {}
    }
    hiveOptions.value = opts
  } catch (e) {
    showError(apiError(e, 'Chargement du suivi sanitaire impossible'))
    console.error(e)
  }
}

function openTreatment() {
  editId.value = null
  form.value = { ...defaultForm, record_type: 'treatment', application_date: new Date().toISOString().slice(0, 10) }
  showTreatmentForm.value = true
}

function openVarroa() {
  editId.value = null
  form.value = { ...defaultForm, record_type: 'varroa_count', hive_ids: [], application_date: new Date().toISOString().slice(0, 10) }
  showVarroaForm.value = true
}

function editRecord(r) {
  editId.value = r.id
  form.value = { ...r, hive_ids: [r.hive_id] }
  if (r.record_type === 'varroa_count') showVarroaForm.value = true
  else showTreatmentForm.value = true
}

async function saveTreatment() {
  if (!editId.value && form.value.hive_ids.length === 0) { showError('Sélectionnez au moins une ruche'); return }
  if (!form.value.treatment_type) { showError('Type de traitement requis'); return }
  saving.value = true
  try {
    if (editId.value) {
      await api.put('/sanitary/' + editId.value, form.value)
    } else {
      await api.post('/sanitary/', { ...form.value, record_type: 'treatment' })
    }
    showTreatmentForm.value = false
    showSuccess('Traitement enregistré')
    await load()
  } catch (e) { showError(apiError(e, 'Erreur')) }
  finally { saving.value = false }
}

async function saveVarroa() {
  if (!editId.value && form.value.hive_ids.length === 0) { showError('Sélectionnez au moins une ruche'); return }
  if (form.value.varroa_count == null) { showError('Nombre de varroas requis'); return }
  saving.value = true
  try {
    if (editId.value) {
      await api.put('/sanitary/' + editId.value, form.value)
    } else {
      await api.post('/sanitary/', { ...form.value, record_type: 'varroa_count', treatment_type: 'Comptage varroa' })
    }
    showVarroaForm.value = false
    showSuccess('Comptage enregistré')
    await load()
  } catch (e) { showError(apiError(e, 'Erreur')) }
  finally { saving.value = false }
}

async function deleteRecord(id) {
  if (!(await confirmAction('Supprimer cet enregistrement ?'))) return
  try {
    await api.delete('/sanitary/' + id)
    showSuccess('Supprimé')
    await load()
  } catch (e) { showError(apiError(e, 'Erreur')) }
}

onMounted(load)
</script>
