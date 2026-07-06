<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Miellée</h2>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNew">
        Nouvelle récolte
      </v-btn>
    </div>

    <!-- Filtre Associatif / Privé -->
    <v-tabs v-model="ownershipTab" class="mb-4" color="primary">
      <v-tab value="">Tout</v-tab>
      <v-tab value="associative">🏛️ Associatif</v-tab>
      <v-tab value="private">🏠 Privé</v-tab>
    </v-tabs>

    <!-- Filtre utilisateur (admins uniquement, onglet privé) -->
    <v-row v-if="ownershipTab === 'private' && canManageAsso" class="mb-3" dense>
      <v-col cols="12" sm="6" md="4">
        <v-select
          v-model="privateUserFilter"
          :items="privateUserOptions"
          item-title="name"
          item-value="id"
          label="Voir les données privées de…"
          density="compact"
          variant="outlined"
          hide-details
          clearable
          prepend-inner-icon="mdi-account-filter"
        />
      </v-col>
    </v-row>

    <!-- COMPTEURS PAR TYPE DE MIEL -->
    <v-card class="mb-4 pa-4" variant="outlined">
      <v-card-title class="text-subtitle-1 d-flex align-center">
        <v-icon class="mr-2">mdi-beehive-outline</v-icon> Récolte par type de miel
      </v-card-title>
      <v-card-text>
        <v-row v-if="honeyByCategory.length" dense>
          <v-col v-for="hc in honeyByCategory" :key="hc.category" cols="6" sm="3">
            <v-card variant="tonal" color="amber" class="text-center pa-2">
              <div class="text-h6 font-weight-bold">{{ hc.total_kg.toFixed(1) }} kg</div>
              <div class="text-caption font-weight-medium">{{ hc.category }}</div>
              <div class="text-caption text-grey">mis en pot : {{ hc.jarred_kg.toFixed(1) }} kg</div>
              <div class="text-caption" :class="hc.remaining_kg > 0 ? 'text-success' : 'text-grey'">
                reste : {{ hc.remaining_kg.toFixed(1) }} kg
              </div>
            </v-card>
          </v-col>
        </v-row>
        <p v-else class="text-grey text-center">Aucune récolte enregistrée</p>
      </v-card-text>
    </v-card>

    <!-- STOCK DE POTS -->
    <v-card class="mb-4 pa-4" variant="outlined">
      <v-card-title class="text-subtitle-1 d-flex align-center">
        <v-icon class="mr-2">mdi-jar-outline</v-icon> Stock de pots
        <v-spacer />
        <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="openNewJar">Mise en pot</v-btn>
      </v-card-title>
      <v-card-text>
        <v-row v-if="jarStock.length" dense>
          <v-col v-for="js in jarStock" :key="js.jar_weight_g + js.ownership" cols="6" sm="3">
            <v-card variant="tonal" :color="js.ownership === 'associative' ? 'blue' : 'orange'" class="text-center pa-2">
              <div class="text-h6 font-weight-bold">{{ js.stock }}</div>
              <div class="text-caption">Pot {{ js.jar_weight_g }}g</div>
              <div class="text-caption text-grey">{{ js.ownership === 'associative' ? '🏛️' : '🏠' }} · vendus: {{ js.sold }}</div>
            </v-card>
          </v-col>
        </v-row>
        <p v-else class="text-grey text-center">Aucun pot en stock</p>
      </v-card-text>
    </v-card>

    <!-- VENTES -->
    <v-card class="mb-4 pa-4" variant="outlined">
      <v-card-title class="text-subtitle-1 d-flex align-center">
        <v-icon class="mr-2">mdi-cash-register</v-icon> Ventes de miel
        <v-spacer />
        <v-btn size="small" color="success" prepend-icon="mdi-plus" @click="openNewSale">Nouvelle vente</v-btn>
      </v-card-title>
      <v-data-table v-if="sales.length" :headers="saleHeaders" :items="sales" density="compact">
        <template v-slot:item.sold_at="{ item }">{{ new Date(item.sold_at).toLocaleDateString('fr-FR') }}</template>
        <template v-slot:item.total_amount="{ item }"><v-chip color="success" size="small">{{ item.total_amount.toFixed(2) }} €</v-chip></template>
        <template v-slot:item.ownership="{ item }">
          <v-chip :color="item.ownership === 'associative' ? 'blue' : 'orange'" size="x-small">{{ item.ownership === 'associative' ? 'Asso' : 'Privé' }}</v-chip>
        </template>
      </v-data-table>
      <v-card-text v-else><p class="text-grey text-center">Aucune vente enregistrée</p></v-card-text>
    </v-card>

    <!-- Tableau des récoltes -->
    <v-card class="mb-4 pa-4">
      <v-card-title class="text-subtitle-1">Récoltes</v-card-title>
      <v-data-table :headers="headers" :items="harvests" density="compact">
        <template v-slot:item.harvest_date="{ item }">{{ new Date(item.harvest_date).toLocaleDateString('fr-FR') }}</template>
        <template v-slot:item.quantity_kg="{ item }"><v-chip color="amber" size="small">{{ item.quantity_kg }} kg</v-chip></template>
        <template v-slot:item.ownership="{ item }">
          <v-chip :color="item.ownership === 'associative' ? 'blue' : 'orange'" size="x-small">{{ item.ownership === 'associative' ? 'Asso' : 'Privé' }}</v-chip>
        </template>
        <template v-slot:item.category_name="{ item }">{{ item.category_name || '—' }}</template>
        <template v-slot:item.jars="{ item }">
          <span v-if="item.jars?.length">{{ item.jars.map(j => j.quantity + 'x' + j.jar_weight_g + 'g').join(', ') }}</span>
          <span v-else class="text-grey">—</span>
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn icon size="small" @click="editHarvest(item)"><v-icon>mdi-pencil</v-icon></v-btn>
          <v-btn v-if="auth.isAdmin" icon size="small" @click="deleteHarvest(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Admin catégories -->
    <v-card v-if="auth.isAdmin" class="mt-4 pa-4" variant="outlined">
      <v-card-title class="text-subtitle-1"><v-icon class="mr-1">mdi-tag-multiple</v-icon> Catégories de miel (Admin)</v-card-title>
      <v-card-text>
        <v-chip v-for="cat in categories" :key="cat.id" class="mr-2 mb-2" closable @click:close="deleteCategory(cat.id)">{{ cat.name }}</v-chip>
        <div class="d-flex ga-2 mt-2" style="max-width:400px;">
          <v-text-field v-model="newCatName" label="Nouvelle catégorie" density="compact" hide-details />
          <v-btn color="primary" @click="addCategory" :disabled="!newCatName">Ajouter</v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Dialog récolte -->
    <v-dialog v-model="showForm" max-width="550">
      <v-card>
        <v-card-title>{{ editId ? 'Modifier' : 'Nouvelle' }} récolte</v-card-title>
        <v-card-text>
          <v-btn-toggle v-model="form.ownership" mandatory class="mb-3 d-flex">
            <v-btn value="associative" color="blue" class="flex-grow-1" :disabled="!canManageAsso">🏛️ Associatif</v-btn>
            <v-btn value="private" color="orange" class="flex-grow-1">🏠 Privé</v-btn>
          </v-btn-toggle>
          <v-select v-model="form.category_id" :items="categories" item-title="name" item-value="id" label="Catégorie de miel" clearable />
          <v-select v-model="form.apiary_id" :items="apiaries" item-title="name" item-value="id" label="Rucher" clearable />
          <v-text-field v-model.number="form.quantity_kg" label="Quantité (kg)" type="number" step="0.1" required />
          <v-row>
            <v-col><v-text-field v-model.number="form.nb_supers" label="Nb hausses" type="number" /></v-col>
            <v-col><v-text-field v-model.number="form.nb_frames" label="Nb cadres" type="number" /></v-col>
          </v-row>
          <v-text-field v-model="form.harvest_date" label="Date de récolte" type="date" />
          <v-textarea v-model="form.notes" label="Notes" rows="2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer /><v-btn @click="showForm = false">Annuler</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog mise en pot -->
    <v-dialog v-model="showJarForm" max-width="450">
      <v-card>
        <v-card-title>Mise en pot</v-card-title>
        <v-card-text>
          <v-select v-model="jarForm.harvest_id" :items="harvests" :item-title="h => new Date(h.harvest_date).toLocaleDateString('fr-FR') + ' — ' + h.quantity_kg + 'kg ' + (h.category_name || '')" item-value="id" label="Récolte source" />
          <v-btn-toggle v-model="jarForm.ownership" mandatory class="mb-3 d-flex">
            <v-btn value="associative" color="blue" class="flex-grow-1" :disabled="!canManageAsso">🏛️ Asso</v-btn>
            <v-btn value="private" color="orange" class="flex-grow-1">🏠 Privé</v-btn>
          </v-btn-toggle>
          <v-select v-model="jarForm.jar_weight_g" :items="jarSizes" label="Format du pot" />
          <v-text-field v-model.number="jarForm.quantity" label="Nombre de pots" type="number" min="1" />
          <v-text-field v-model.number="jarForm.unit_price" label="Prix unitaire (€)" type="number" step="0.5" />
        </v-card-text>
        <v-card-actions>
          <v-spacer /><v-btn @click="showJarForm = false">Annuler</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveJar">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog vente -->
    <v-dialog v-model="showSaleForm" max-width="450">
      <v-card>
        <v-card-title>Vente de miel</v-card-title>
        <v-card-text>
          <v-select v-model="saleForm.jar_id" :items="availableJars" :item-title="j => j.jar_weight_g + 'g — stock: ' + j.quantity + ' (' + (j.ownership === 'associative' ? 'Asso' : 'Privé') + ')'" item-value="id" label="Pot à vendre" />
          <v-text-field v-model.number="saleForm.quantity" label="Quantité" type="number" min="1" />
          <v-text-field v-model.number="saleForm.unit_price" label="Prix unitaire (€)" type="number" step="0.5" />
          <v-text-field v-model="saleForm.buyer" label="Acheteur (optionnel)" />
        </v-card-text>
        <v-card-actions>
          <v-spacer /><v-btn @click="showSaleForm = false">Annuler</v-btn>
          <v-btn color="success" :loading="saving" @click="saveSale">Vendre</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="errorSnack" color="error" timeout="4000">{{ errorMsg }}</v-snackbar>
    <v-snackbar v-model="successSnack" color="success" timeout="2000">{{ successMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const canManageAsso = computed(() => auth.hasRole('yard_manager') || auth.hasRole('treasurer'))
const harvests = ref([])
const categories = ref([])
const apiaries = ref([])
const stats = ref({})
const jarStock = ref([])
const jars = ref([])
const sales = ref([])
const ownershipTab = ref('')
const privateUserFilter = ref(null)
const privateUsers = ref([])

const privateUserOptions = computed(() => [
  { id: null, name: '👥 Tous les utilisateurs' },
  ...privateUsers.value,
])

const showForm = ref(false)
const showJarForm = ref(false)
const showSaleForm = ref(false)
const editId = ref(null)
const saving = ref(false)
const errorSnack = ref(false)
const errorMsg = ref('')
const successSnack = ref(false)
const successMsg = ref('')
const newCatName = ref('')
const currentYear = new Date().getFullYear()

const jarSizes = [
  { title: '1 kg (1000g)', value: 1000 },
  { title: '500g', value: 500 },
  { title: '250g', value: 250 },
  { title: '125g', value: 125 },
]

const defaultOwnership = computed(() => canManageAsso.value ? 'associative' : 'private')
const defaultForm = { category_id: null, apiary_id: null, ownership: 'private', quantity_kg: 0, nb_supers: null, nb_frames: null, harvest_date: '', notes: '' }
const form = ref({ ...defaultForm })
const jarForm = ref({ harvest_id: null, ownership: 'associative', jar_weight_g: 500, quantity: 1, unit_price: null })
const saleForm = ref({ jar_id: null, quantity: 1, unit_price: null, buyer: '' })

const headers = [
  { title: 'Date', key: 'harvest_date' },
  { title: 'Type', key: 'ownership' },
  { title: 'Catégorie', key: 'category_name' },
  { title: 'Rucher', key: 'apiary_name' },
  { title: 'Quantité', key: 'quantity_kg' },
  { title: 'Pots', key: 'jars', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false },
]

const saleHeaders = [
  { title: 'Date', key: 'sold_at' },
  { title: 'Type', key: 'ownership' },
  { title: 'Format', key: 'jar_weight_g' },
  { title: 'Qté', key: 'quantity' },
  { title: 'P.U.', key: 'unit_price' },
  { title: 'Total', key: 'total_amount' },
  { title: 'Acheteur', key: 'buyer' },
]

const monthLabels = ['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc']

const monthlyData = computed(() => {
  const data = Array.from({ length: 12 }, (_, i) => ({ month: i + 1, kg: 0, label: monthLabels[i] }))
  if (stats.value.by_month) {
    for (const m of stats.value.by_month) data[m.month - 1].kg = m.total_kg
  }
  const maxKg = Math.max(...data.map(d => d.kg), 1)
  return data.map(d => ({ ...d, height: (d.kg / maxKg) * 100 }))
})

const availableJars = computed(() => jars.value.filter(j => j.quantity > 0))

const honeyByCategory = computed(() => {
  const map = {}
  for (const h of harvests.value) {
    const cat = h.category_name || 'Non catégorisé'
    if (!map[cat]) map[cat] = { category: cat, total_kg: 0, jarred_kg: 0 }
    map[cat].total_kg += h.quantity_kg || 0
    // Calculer le poids mis en pot depuis les jars de cette récolte
    if (h.jars) {
      for (const j of h.jars) {
        map[cat].jarred_kg += (j.quantity * j.jar_weight_g) / 1000
      }
    }
  }
  return Object.values(map).map(c => ({ ...c, remaining_kg: c.total_kg - c.jarred_kg }))
})

function showError(msg) { errorMsg.value = msg; errorSnack.value = true }
function showSuccess(msg) { successMsg.value = msg; successSnack.value = true }

async function load() {
  const own = ownershipTab.value || undefined
  const uid = (own === 'private' && canManageAsso.value && privateUserFilter.value) ? privateUserFilter.value : undefined
  try {
    const params = { ownership: own, user_id: uid }
    const requests = [
      api.get('/honey/', { params }),
      api.get('/honey/categories'),
      api.get('/honey/stats', { params }),
      api.get('/apiaries/'),
      api.get('/honey/jars/stock', { params }),
      api.get('/honey/jars', { params }),
      api.get('/honey/sales', { params }),
    ]
    // Charger la liste des users privés si admin et pas encore chargée
    if (canManageAsso.value && privateUsers.value.length === 0) {
      requests.push(api.get('/honey/private-users'))
    }
    const results = await Promise.all(requests)
    harvests.value = results[0].data
    categories.value = results[1].data
    stats.value = results[2].data
    apiaries.value = results[3].data
    jarStock.value = results[4].data
    jars.value = results[5].data
    sales.value = results[6].data
    if (results[7]) privateUsers.value = results[7].data
  } catch (e) {
    showError('Erreur de chargement')
    console.error(e)
  }
}

watch(ownershipTab, () => load())
watch(privateUserFilter, () => load())

function openNew() {
  editId.value = null
  form.value = { ...defaultForm, ownership: defaultOwnership.value }
  showForm.value = true
}

function editHarvest(h) {
  editId.value = h.id
  form.value = { category_id: h.category_id, apiary_id: h.apiary_id, ownership: h.ownership, quantity_kg: h.quantity_kg, nb_supers: h.nb_supers, nb_frames: h.nb_frames, harvest_date: h.harvest_date ? h.harvest_date.substring(0, 10) : '', notes: h.notes || '' }
  showForm.value = true
}

async function save() {
  if (!form.value.quantity_kg || form.value.quantity_kg <= 0) { showError('Quantité requise'); return }
  saving.value = true
  try {
    const payload = { ...form.value }
    if (payload.harvest_date) payload.harvest_date = new Date(payload.harvest_date).toISOString()
    else delete payload.harvest_date
    if (editId.value) await api.put('/honey/' + editId.value, payload)
    else await api.post('/honey/', payload)
    showForm.value = false
    showSuccess('Récolte enregistrée')
    await load()
  } catch (e) { showError(e.response?.data?.detail || 'Erreur') }
  finally { saving.value = false }
}

async function deleteHarvest(id) {
  if (!confirm('Supprimer cette récolte ?')) return
  try { await api.delete('/honey/' + id); showSuccess('Supprimée'); await load() }
  catch (e) { showError(e.response?.data?.detail || 'Erreur') }
}

function openNewJar() { jarForm.value = { harvest_id: null, ownership: 'associative', jar_weight_g: 500, quantity: 1, unit_price: null }; showJarForm.value = true }

async function saveJar() {
  if (!jarForm.value.harvest_id || jarForm.value.quantity < 1) { showError('Récolte et quantité requises'); return }
  saving.value = true
  try {
    await api.post('/honey/jars', jarForm.value)
    showJarForm.value = false
    showSuccess('Pots enregistrés')
    await load()
  } catch (e) { showError(e.response?.data?.detail || 'Erreur') }
  finally { saving.value = false }
}

function openNewSale() {
  saleForm.value = { jar_id: null, quantity: 1, unit_price: null, buyer: '' }
  showSaleForm.value = true
}

async function saveSale() {
  if (!saleForm.value.jar_id || saleForm.value.quantity < 1) { showError('Pot et quantité requis'); return }
  saving.value = true
  try {
    await api.post('/honey/sales', saleForm.value)
    showSaleForm.value = false
    showSuccess('Vente enregistrée (compta mise à jour)')
    await load()
  } catch (e) { showError(e.response?.data?.detail || 'Erreur') }
  finally { saving.value = false }
}

async function addCategory() {
  if (!newCatName.value) return
  try { await api.post('/honey/categories', { name: newCatName.value }); newCatName.value = ''; showSuccess('Catégorie ajoutée'); await load() }
  catch (e) { showError(e.response?.data?.detail || 'Erreur') }
}

async function deleteCategory(id) {
  if (!confirm('Supprimer ?')) return
  try { await api.delete('/honey/categories/' + id); await load() }
  catch (e) { showError(e.response?.data?.detail || 'Erreur') }
}

onMounted(load)
</script>
