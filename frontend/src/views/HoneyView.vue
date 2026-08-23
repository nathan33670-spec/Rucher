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
      <v-tab value="associative" prepend-icon="mdi-account-group">Associatif</v-tab>
      <v-tab value="private" prepend-icon="mdi-home">Privé</v-tab>
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
            <v-card variant="tonal" color="primary" class="text-center pa-2">
              <div class="text-h6 font-weight-bold">{{ hc.total_kg.toFixed(1) }} kg</div>
              <div class="text-caption font-weight-medium">{{ hc.category }}</div>
              <div class="text-caption r-muted">mis en pot : {{ hc.jarred_kg.toFixed(1) }} kg</div>
              <div class="text-caption" :class="hc.remaining_kg > 0 ? 'text-success' : 'r-muted'">
                reste à empoter : {{ hc.remaining_kg.toFixed(1) }} kg
              </div>
              <div v-if="hc.over_potted" class="text-caption text-error" title="La quantité empotée dépasse la récolte : vérifiez vos saisies.">
                <v-icon size="12">mdi-alert</v-icon> empoté &gt; récolté
              </div>
            </v-card>
          </v-col>
        </v-row>
        <p v-else class="r-muted text-center">Aucune récolte enregistrée</p>
      </v-card-text>
    </v-card>

    <!-- STOCK DE POTS — un bloc par lot (récolte + format) -->
    <v-card class="mb-4" variant="outlined">
      <v-card-title class="d-flex align-center flex-wrap ga-2">
        <v-icon class="mr-2" color="primary">mdi-bottle-tonic-outline</v-icon>
        <span>Stock de pots</span>
        <v-chip v-if="jarStock.length" size="x-small" variant="tonal" class="ml-1">
          {{ jarStock.length }} lot{{ jarStock.length > 1 ? 's' : '' }}
        </v-chip>
        <v-spacer />
        <v-btn size="small" variant="tonal" color="primary" prepend-icon="mdi-plus" @click="openNewJar">
          Mise en pot
        </v-btn>
        <v-btn size="small" color="success" prepend-icon="mdi-cash-plus"
          :disabled="!availableJars.length" @click="openNewSale">
          Nouvelle vente
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Totaux : l'information la plus consultée, en tête -->
        <v-row v-if="jarStock.length" dense class="mb-3">
          <v-col cols="4">
            <div class="totals-tile">
              <div class="r-stat-value text-primary">{{ totalStock }}</div>
              <div class="r-stat-label">pots en stock</div>
            </div>
          </v-col>
          <v-col cols="4">
            <div class="totals-tile">
              <div class="r-stat-value text-success">{{ totalSold }}</div>
              <div class="r-stat-label">pots vendus</div>
            </div>
          </v-col>
          <v-col cols="4">
            <div class="totals-tile">
              <div class="r-stat-value">{{ totalKg.toFixed(1) }} kg</div>
              <div class="r-stat-label">équivalent en stock</div>
            </div>
          </v-col>
        </v-row>

        <v-row v-if="jarStock.length" dense>
          <v-col v-for="js in jarStock" :key="js.lot + js.jar_weight_g + js.ownership" cols="12" sm="6" md="4">
            <v-card class="lot-card pa-3" :class="{ 'lot-card--empty': js.stock === 0 }">
              <!-- En-tête du lot : sa référence et son type -->
              <div class="d-flex align-center ga-2 mb-2">
                <v-chip size="x-small" variant="tonal" color="secondary" class="font-weight-bold">
                  {{ js.lot }}
                </v-chip>
                <v-spacer />
                <v-chip size="x-small" variant="tonal"
                  :color="js.ownership === 'associative' ? 'info' : 'accent'">
                  {{ js.ownership === 'associative' ? 'Associatif' : 'Privé' }}
                </v-chip>
              </div>

              <!-- Chiffre principal : ce qu'il reste -->
              <div class="d-flex align-end ga-2">
                <div class="lot-stock">{{ js.stock }}</div>
                <div class="pb-1">
                  <div class="text-body-2 font-weight-bold">pot{{ js.stock > 1 ? 's' : '' }} de {{ js.jar_weight_g }}g</div>
                  <div class="text-caption r-muted">{{ js.category }}</div>
                </div>
              </div>

              <!-- Écoulement du lot -->
              <v-progress-linear
                :model-value="js.initial ? (js.sold / js.initial) * 100 : 0"
                color="success" bg-color="surface-variant" height="6" rounded class="my-2"
              />
              <div class="d-flex align-center text-caption flex-wrap ga-1">
                <span class="font-weight-bold text-success">{{ js.sold }} vendu{{ js.sold > 1 ? 's' : '' }}</span>
                <span class="r-muted">sur {{ js.initial }} empoté{{ js.initial > 1 ? 's' : '' }}</span>
                <v-spacer />
                <span v-if="js.unit_price" class="font-weight-bold">{{ money(js.unit_price) }}</span>
              </div>

              <div class="text-caption r-muted mt-1">
                <v-icon size="12">mdi-calendar</v-icon>
                Récolte du {{ new Date(js.harvest_date).toLocaleDateString('fr-FR') }}
                <template v-if="js.owner_name"> · {{ js.owner_name }}</template>
              </div>
            </v-card>
          </v-col>
        </v-row>
        <p v-else class="r-muted text-center py-4">Aucun pot en stock</p>
      </v-card-text>
    </v-card>

    <!-- HISTORIQUES — repliés par défaut : ces tableaux sont longs et ne
         servent qu'à la consultation ponctuelle. -->
    <v-expansion-panels v-model="openPanels" multiple class="mb-4">

      <!-- Historique des ventes -->
      <v-expansion-panel value="sales" rounded="lg">
        <v-expansion-panel-title>
          <v-icon class="mr-2" color="primary">mdi-cash-register</v-icon>
          <span class="font-weight-bold">Historique des ventes</span>
          <v-chip size="x-small" variant="tonal" class="ml-2">{{ sales.length }}</v-chip>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-data-table v-if="sales.length" :headers="saleHeaders" :items="sales" density="compact">
            <template v-slot:item.sold_at="{ item }">{{ new Date(item.sold_at).toLocaleDateString('fr-FR') }}</template>
            <template v-slot:item.total_amount="{ item }"><v-chip color="success" size="small" variant="tonal">{{ money(item.total_amount) }}</v-chip></template>
            <template v-slot:item.lot="{ item }">
              <v-chip size="x-small" variant="tonal" color="secondary">{{ lotOf(item) }}</v-chip>
            </template>
            <template v-slot:item.unit_price="{ item }">{{ money(item.unit_price) }}</template>
            <template v-slot:item.buyer="{ item }">{{ item.buyer || '—' }}</template>
            <template v-slot:item.ownership="{ item }">
              <v-chip :color="item.ownership === 'associative' ? 'info' : 'accent'" size="x-small" variant="tonal">{{ item.ownership === 'associative' ? 'Associatif' : 'Privé' }}</v-chip>
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon size="small" variant="text" title="Modifier" @click="editSale(item)"><v-icon>mdi-pencil</v-icon></v-btn>
              <v-btn icon size="small" variant="text" title="Annuler la vente" @click="deleteSale(item)"><v-icon color="error">mdi-delete</v-icon></v-btn>
            </template>
          </v-data-table>
          <p v-else class="r-muted text-center py-4">Aucune vente enregistrée</p>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <!-- Historique des récoltes -->
      <v-expansion-panel value="harvests" rounded="lg">
        <v-expansion-panel-title>
          <v-icon class="mr-2" color="primary">mdi-beehive-outline</v-icon>
          <span class="font-weight-bold">Historique des récoltes</span>
          <v-chip size="x-small" variant="tonal" class="ml-2">{{ harvests.length }}</v-chip>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
      <v-data-table :headers="headers" :items="harvests" density="compact">
        <template v-slot:item.harvest_date="{ item }">{{ new Date(item.harvest_date).toLocaleDateString('fr-FR') }}</template>
        <template v-slot:item.quantity_kg="{ item }"><v-chip color="primary" size="small" variant="tonal">{{ item.quantity_kg }} kg</v-chip></template>
        <template v-slot:item.ownership="{ item }">
          <v-chip :color="item.ownership === 'associative' ? 'info' : 'accent'" size="x-small" variant="tonal">{{ item.ownership === 'associative' ? 'Associatif' : 'Privé' }}</v-chip>
        </template>
        <template v-slot:item.category_name="{ item }">{{ item.category_name || '—' }}</template>
        <template v-slot:item.jars="{ item }">
          <template v-if="item.jars?.length">
            <v-chip
              v-for="j in item.jars" :key="j.id"
              size="x-small" variant="tonal" class="mr-1"
              :color="j.quantity > 0 ? 'primary' : 'secondary'"
              :title="`${j.initial_quantity ?? j.quantity} pot(s) de ${j.jar_weight_g}g empotés, ${j.quantity} encore en stock`"
            >
              {{ j.quantity }}/{{ j.initial_quantity ?? j.quantity }} × {{ j.jar_weight_g }}g
            </v-chip>
          </template>
          <span v-else class="r-muted">—</span>
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn icon size="small" variant="text" @click="editHarvest(item)"><v-icon>mdi-pencil</v-icon></v-btn>
          <v-btn v-if="auth.isAdmin" icon size="small" variant="text" @click="deleteHarvest(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
        </template>
      </v-data-table>
        </v-expansion-panel-text>
      </v-expansion-panel>

    </v-expansion-panels>

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
            <v-btn value="associative" color="info" class="flex-grow-1" :disabled="!canManageAsso" prepend-icon="mdi-account-group">Associatif</v-btn>
            <v-btn value="private" color="accent" class="flex-grow-1" prepend-icon="mdi-home">Privé</v-btn>
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
          <v-select v-model="jarForm.harvest_id" :items="harvests" :item-title="harvestLabel" item-value="id" label="Récolte source (lot)"
            hint="Chaque récolte constitue un lot distinct : les pots restent traçables jusqu'à la vente."
            persistent-hint class="mb-2" />
          <v-btn-toggle v-model="jarForm.ownership" mandatory class="mb-3 d-flex">
            <v-btn value="associative" color="info" class="flex-grow-1" :disabled="!canManageAsso" prepend-icon="mdi-account-group">Associatif</v-btn>
            <v-btn value="private" color="accent" class="flex-grow-1" prepend-icon="mdi-home">Privé</v-btn>
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
        <v-card-title>{{ saleEditId ? 'Modifier la vente' : 'Vente de miel' }}</v-card-title>
        <v-card-text>
          <!-- Le pot n'est pas modifiable après coup : changer de pot
               reviendrait à annuler la vente et à en saisir une autre. -->
          <v-select
            v-if="!saleEditId"
            v-model="saleForm.jar_id" :items="availableJars"
            :item-title="jarLabel"
            item-value="id" label="Pot à vendre"
          />
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-4">
            Pot de {{ saleEditJar }}. Pour changer de pot, annulez cette vente
            et saisissez-en une nouvelle.
          </v-alert>
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
import { money } from '../services/format'
import { confirmAction } from '../services/confirm'
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
  { id: null, name: 'Tous les utilisateurs' },
  ...privateUsers.value,
])

const showForm = ref(false)
const showJarForm = ref(false)
const showSaleForm = ref(false)
const saleEditId = ref(null)
const saleEditJar = ref('')
// Historiques repliés à l'ouverture de la page.
const openPanels = ref([])
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
  { title: 'Lot', key: 'lot', sortable: false },
  { title: 'Format', key: 'jar_weight_g' },
  { title: 'Qté', key: 'quantity' },
  { title: 'P.U.', key: 'unit_price' },
  { title: 'Total', key: 'total_amount' },
  { title: 'Acheteur', key: 'buyer' },
  { title: 'Actions', key: 'actions', sortable: false },
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

// Totaux mis en tête de la carte : ce sont les chiffres les plus consultés.
const totalStock = computed(() => jarStock.value.reduce((n, j) => n + (j.stock || 0), 0))
const totalSold = computed(() => jarStock.value.reduce((n, j) => n + (j.sold || 0), 0))
const totalKg = computed(() =>
  jarStock.value.reduce((n, j) => n + ((j.stock || 0) * j.jar_weight_g) / 1000, 0))

const honeyByCategory = computed(() => {
  const map = {}
  for (const h of harvests.value) {
    const cat = h.category_name || 'Non catégorisé'
    if (!map[cat]) map[cat] = { category: cat, total_kg: 0, jarred_kg: 0 }
    map[cat].total_kg += h.quantity_kg || 0
    // Poids mis en pot : on compte la quantité INITIALEMENT empotée, pas le
    // stock restant. Vendre un pot ne remet pas le miel dans la récolte —
    // utiliser « quantity » faisait remonter le « reste » à chaque vente.
    if (h.jars) {
      for (const j of h.jars) {
        map[cat].jarred_kg += ((j.initial_quantity ?? j.quantity) * j.jar_weight_g) / 1000
      }
    }
  }
  return Object.values(map).map(c => ({
    ...c,
    // Le reste ne peut pas être négatif : au-delà du volume récolté, c'est une
    // saisie à corriger, pas un stock.
    remaining_kg: Math.max(0, c.total_kg - c.jarred_kg),
    over_potted: c.jarred_kg > c.total_kg + 0.001,
  }))
})

// Libellés des sélecteurs : la référence de lot doit être visible partout où
// l'on choisit des pots, sinon on ignore quelle récolte on écoule.
/** Référence du lot d'une vente, retrouvée via le pot vendu. */
function lotOf(sale) {
  return jars.value.find(j => j.id === sale.jar_id)?.lot || '—'
}

function jarLabel(j) {
  const own = j.ownership === 'associative' ? 'Associatif' : 'Privé'
  return `${j.lot || 'lot ?'} · ${j.jar_weight_g}g — ${j.quantity} en stock (${own})`
}

function harvestLabel(h) {
  const d = new Date(h.harvest_date).toLocaleDateString('fr-FR')
  const potted = (h.jars || []).reduce(
    (n, j) => n + ((j.initial_quantity ?? j.quantity) * j.jar_weight_g) / 1000, 0)
  const left = Math.max(0, (h.quantity_kg || 0) - potted)
  return `${d} — ${h.quantity_kg} kg ${h.category_name || ''} · reste ${left.toFixed(1)} kg`
}

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
  if (!(await confirmAction('Supprimer cette récolte ?'))) return
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
  saleEditId.value = null
  saleEditJar.value = ''
  saleForm.value = { jar_id: null, quantity: 1, unit_price: null, buyer: '' }
  showSaleForm.value = true
}

function editSale(sale) {
  saleEditId.value = sale.id
  const j = jars.value.find(x => x.id === sale.jar_id)
  saleEditJar.value = (j?.lot ? `${j.lot} · ` : '') + `${sale.jar_weight_g}g`
    + (sale.category_name ? ` — ${sale.category_name}` : '')
  saleForm.value = {
    jar_id: sale.jar_id,
    quantity: sale.quantity,
    unit_price: sale.unit_price,
    buyer: sale.buyer || '',
  }
  showSaleForm.value = true
}

async function saveSale() {
  if (!saleEditId.value && !saleForm.value.jar_id) { showError('Pot requis'); return }
  if (saleForm.value.quantity < 1) { showError('Quantité requise'); return }
  saving.value = true
  try {
    if (saleEditId.value) {
      await api.put(`/honey/sales/${saleEditId.value}`, {
        quantity: saleForm.value.quantity,
        unit_price: saleForm.value.unit_price,
        buyer: saleForm.value.buyer,
      })
      showSuccess('Vente modifiée (stock et compta mis à jour)')
    } else {
      await api.post('/honey/sales', saleForm.value)
      showSuccess('Vente enregistrée (compta mise à jour)')
    }
    showSaleForm.value = false
    await load()
  } catch (e) { showError(e.response?.data?.detail || 'Erreur') }
  finally { saving.value = false }
}

async function deleteSale(sale) {
  const ok = await confirmAction(
    `Annuler cette vente de ${sale.quantity} pot(s) ? Les pots retournent en stock` +
    (sale.ownership === 'associative' ? " et l'écriture comptable est supprimée." : '.')
  )
  if (!ok) return
  try {
    await api.delete(`/honey/sales/${sale.id}`)
    showSuccess('Vente annulée, pots remis en stock')
    await load()
  } catch (e) { showError(e.response?.data?.detail || 'Erreur') }
}

async function addCategory() {
  if (!newCatName.value) return
  try { await api.post('/honey/categories', { name: newCatName.value }); newCatName.value = ''; showSuccess('Catégorie ajoutée'); await load() }
  catch (e) { showError(e.response?.data?.detail || 'Erreur') }
}

async function deleteCategory(id) {
  if (!(await confirmAction('Supprimer ?'))) return
  try { await api.delete('/honey/categories/' + id); await load() }
  catch (e) { showError(e.response?.data?.detail || 'Erreur') }
}

onMounted(load)
</script>

<style scoped>
/* Totaux : lecture immédiate, sans concurrence visuelle avec les lots. */
.totals-tile {
  text-align: center;
  padding: 10px 6px;
  border-radius: 12px;
  background: rgba(198, 138, 18, 0.07);
}

/* Un lot = une carte. Le liseré rappelle qu'il s'agit d'une unité traçable. */
.lot-card {
  height: 100%;
  border-left: 3px solid #9A6B0F !important;
}

/* Lot écoulé : présent pour l'historique, mais visuellement en retrait. */
.lot-card--empty {
  opacity: 0.62;
  border-left-color: rgba(93, 64, 55, 0.3) !important;
}

.lot-stock {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1;
  color: #9A6B0F;
}
</style>
