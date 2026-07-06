<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Inventaire</h2>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNewItem" v-if="auth.isAdmin || auth.hasRole('yard_manager') || auth.hasRole('treasurer')">
        Nouvel article
      </v-btn>
    </div>

    <!-- Alertes stock -->
    <v-alert v-for="a in stockAlerts" :key="a.id" type="warning" density="compact" class="mb-2">
      ⚠️ {{ a.name }} : {{ a.quantity }} restants (seuil : {{ a.threshold }})
    </v-alert>

    <!-- Résumé par emplacement -->
    <v-row v-if="locationSummary.length > 0" class="mb-4">
      <v-col v-for="loc in locationSummary" :key="loc.location" cols="12" sm="6" md="3">
        <v-card variant="tonal" :color="loc.location === 'Non assigné' ? 'grey' : 'info'" @click="filterLocation = loc.location === 'Non assigné' ? null : loc.location">
          <v-card-text class="text-center">
            <v-icon size="28" class="mb-1">mdi-warehouse</v-icon>
            <div class="text-subtitle-2 font-weight-bold">{{ loc.location }}</div>
            <div class="text-caption">{{ loc.item_count }} articles · {{ loc.total_qty }} unités</div>
            <div class="text-caption font-weight-bold">{{ loc.total_value.toFixed(2) }} €</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recherche + filtre -->
    <v-row class="mb-3" dense>
      <v-col cols="12" sm="6" md="4">
        <v-text-field
          v-model="searchQuery"
          label="Rechercher un matériel"
          prepend-inner-icon="mdi-magnify"
          clearable
          density="compact"
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-select
          v-if="locations.length > 0"
          v-model="filterLocation"
          :items="locationOptions"
          label="Emplacement"
          clearable
          density="compact"
          hide-details
        />
      </v-col>
    </v-row>

    <v-data-table :headers="headers" :items="filteredItems" density="compact" :search="searchQuery">
      <template v-slot:item.quantity="{ item }">
        <v-chip :color="item.alert_threshold && item.quantity <= item.alert_threshold ? 'error' : 'success'" size="small">
          {{ item.quantity }} {{ item.unit }}
        </v-chip>
      </template>
      <template v-slot:item.location="{ item }">
        <v-chip v-if="item.location" size="small" variant="tonal" color="info">
          <v-icon start size="14">mdi-map-marker</v-icon>
          {{ item.location }}
        </v-chip>
        <span v-else class="text-grey">—</span>
      </template>
      <template v-slot:item.actions="{ item }">
        <template v-if="canEdit">
          <v-btn icon size="small" color="success" title="Entrée" @click.stop="openMovement(item, 'in')"><v-icon>mdi-plus</v-icon></v-btn>
          <v-btn icon size="small" color="error" title="Sortie" @click.stop="openMovement(item, 'out')"><v-icon>mdi-minus</v-icon></v-btn>
          <v-btn icon size="small" color="indigo" title="Déplacer" @click.stop="openMove(item)"><v-icon>mdi-swap-horizontal</v-icon></v-btn>
          <v-btn icon size="small" title="Modifier" @click.stop="editItem(item)"><v-icon>mdi-pencil</v-icon></v-btn>
          <v-btn v-if="auth.isAdmin" icon size="small" title="Supprimer" @click.stop="deleteItem(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
        </template>
      </template>
    </v-data-table>

    <!-- Dialog article -->
    <v-dialog v-model="showItemForm" max-width="500">
      <v-card>
        <v-card-title>{{ itemEditId ? 'Modifier' : 'Nouvel' }} article</v-card-title>
        <v-card-text>
          <v-select
            v-model="nameSelect"
            :items="nameOptions"
            label="Nom"
            placeholder="Choisir ou créer un nom"
            required
            @update:model-value="onNameSelect"
          />
          <v-text-field
            v-if="nameSelect === NEW_OPTION"
            v-model="itemForm.name"
            label="Nouveau nom"
            placeholder="Saisir le nouveau libellé"
            autofocus
          />
          <v-select
            v-model="categorySelect"
            :items="categoryOptions"
            label="Catégorie"
            placeholder="Choisir ou créer une catégorie"
            clearable
            @update:model-value="onCategorySelect"
          />
          <v-text-field
            v-if="categorySelect === NEW_OPTION"
            v-model="itemForm.category"
            label="Nouvelle catégorie"
            placeholder="Saisir la nouvelle catégorie"
          />
          <v-select
            v-model="locationSelect"
            :items="locationFormOptions"
            label="Emplacement"
            placeholder="Choisir ou créer un lieu"
            clearable
            @update:model-value="onLocationSelect"
          />
          <v-text-field
            v-if="locationSelect === NEW_OPTION"
            v-model="itemForm.location"
            label="Nouveau lieu"
            placeholder="ex: Local rucher, Atelier, Hangar..."
            autofocus
          />
          <v-row>
            <v-col><v-text-field v-model.number="itemForm.quantity" label="Quantité" type="number" /></v-col>
            <v-col><v-text-field v-model="itemForm.unit" label="Unité" /></v-col>
          </v-row>
          <v-row>
            <v-col><v-text-field v-model.number="itemForm.unit_price" label="Prix unitaire (€)" type="number" /></v-col>
            <v-col><v-text-field v-model.number="itemForm.alert_threshold" label="Seuil alerte" type="number" /></v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showItemForm = false">Annuler</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveItem">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog mouvement -->
    <v-dialog v-model="showMvt" max-width="400">
      <v-card>
        <v-card-title>{{ mvtType === 'in' ? 'Entrée' : 'Sortie' }} de stock</v-card-title>
        <v-card-text>
          <p class="mb-2"><strong>{{ mvtItem?.name }}</strong></p>
          <p v-if="mvtItem?.location" class="text-caption text-grey mb-2">📍 {{ mvtItem.location }}</p>
          <v-text-field v-model.number="mvtQty" label="Quantité" type="number" min="1" />
          <v-text-field v-model="mvtReason" label="Motif" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showMvt = false">Annuler</v-btn>
          <v-btn :color="mvtType === 'in' ? 'success' : 'error'" :loading="saving" @click="saveMovement">Valider</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog déplacement -->
    <v-dialog v-model="showMoveDialog" max-width="440">
      <v-card>
        <v-card-title>Déplacer un article</v-card-title>
        <v-card-text>
          <p class="mb-1"><strong>{{ moveItem?.name }}</strong></p>
          <p class="text-caption text-grey mb-3">
            Emplacement actuel : {{ moveItem?.location || 'Non assigné' }}
            · Stock disponible : {{ moveItem?.quantity }} {{ moveItem?.unit }}
          </p>

          <v-text-field
            v-model.number="moveQty"
            label="Quantité à déplacer"
            type="number"
            min="1"
            :max="moveItem?.quantity"
            :suffix="moveItem?.unit"
            :hint="moveQty >= (moveItem?.quantity || 0)
              ? 'Tout le stock sera déplacé'
              : 'Déplacement partiel : l\'article sera scindé'"
            persistent-hint
            class="mb-3"
          />

          <v-select
            v-model="moveLocationSelect"
            :items="moveLocationOptions"
            label="Nouvel emplacement"
            placeholder="Choisir ou créer un emplacement"
            @update:model-value="onMoveLocationSelect"
          />
          <v-text-field
            v-if="moveLocationSelect === NEW_OPTION"
            v-model="moveNewLocation"
            label="Nouveau lieu"
            placeholder="ex: Local rucher, Atelier, Hangar..."
            autofocus
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showMoveDialog = false">Annuler</v-btn>
          <v-btn color="indigo" :loading="saving" @click="confirmMove">Déplacer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="errorSnack" color="error" timeout="4000">{{ errorMsg }}</v-snackbar>
    <v-snackbar v-model="successSnack" color="success" timeout="2000">{{ successMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const canEdit = computed(() => auth.isAdmin || auth.hasRole('yard_manager') || auth.hasRole('treasurer'))
const items = ref([])
const stockAlerts = ref([])
const locationSummary = ref([])
const showItemForm = ref(false)
const itemEditId = ref(null)
const saving = ref(false)
const errorSnack = ref(false)
const errorMsg = ref('')
const successSnack = ref(false)
const successMsg = ref('')
const filterLocation = ref(null)
const searchQuery = ref('')

// Move dialog
const showMoveDialog = ref(false)
const moveItem = ref(null)
const moveNewLocation = ref('')
const moveQty = ref(1)
const moveLocationSelect = ref(null)

const defaultItemForm = { name: '', category: '', location: '', quantity: 0, unit: 'unité', unit_price: null, alert_threshold: null }
const itemForm = ref({ ...defaultItemForm })

// Listes déroulantes Nom / Catégorie avec option « nouveau libellé »
const NEW_OPTION = '__new__'
const nameSelect = ref(null)
const categorySelect = ref(null)
const locationSelect = ref(null)

const showMvt = ref(false)
const mvtItem = ref(null)
const mvtType = ref('in')
const mvtQty = ref(1)
const mvtReason = ref('')

const headers = computed(() => {
  const h = [
    { title: 'Nom', key: 'name' },
    { title: 'Catégorie', key: 'category' },
    { title: 'Emplacement', key: 'location' },
    { title: 'Stock', key: 'quantity' },
    { title: 'Prix unit.', key: 'unit_price' },
  ]
  if (canEdit.value) h.push({ title: 'Actions', key: 'actions', sortable: false })
  return h
})

const locations = computed(() => {
  return [...new Set(items.value.map(i => i.location).filter(Boolean))].sort()
})

const locationOptions = computed(() => ['Tous', ...locations.value])

// Noms et catégories existants (pour les listes déroulantes du formulaire)
const names = computed(() =>
  [...new Set(items.value.map(i => i.name).filter(Boolean))].sort((a, b) => a.localeCompare(b))
)
const categories = computed(() =>
  [...new Set(items.value.map(i => i.category).filter(Boolean))].sort((a, b) => a.localeCompare(b))
)
const nameOptions = computed(() => [
  ...names.value.map(n => ({ title: n, value: n })),
  { title: '➕ Nouveau libellé…', value: NEW_OPTION },
])
const categoryOptions = computed(() => [
  ...categories.value.map(c => ({ title: c, value: c })),
  { title: '➕ Nouvelle catégorie…', value: NEW_OPTION },
])

// Options d'emplacement pour le formulaire article (avec création d'un lieu)
const locationFormOptions = computed(() => [
  ...locations.value.map(l => ({ title: l, value: l })),
  { title: '➕ Nouveau lieu…', value: NEW_OPTION },
])
function onLocationSelect(val) {
  itemForm.value.location = (val === NEW_OPTION || val == null) ? '' : val
}

// Options d'emplacement pour le déplacement (avec création d'un nouveau lieu)
const moveLocationOptions = computed(() => [
  ...locations.value.map(l => ({ title: l, value: l })),
  { title: '➕ Nouveau lieu…', value: NEW_OPTION },
])
function onMoveLocationSelect(val) {
  moveNewLocation.value = (val === NEW_OPTION || val == null) ? '' : val
}

// Synchronise la sélection vers itemForm ; « Nouveau… » vide le champ
// pour laisser l'utilisateur saisir un libellé dans le champ texte qui apparaît.
function onNameSelect(val) {
  itemForm.value.name = (val === NEW_OPTION || val == null) ? '' : val
}
function onCategorySelect(val) {
  itemForm.value.category = (val === NEW_OPTION || val == null) ? '' : val
}

const filteredItems = computed(() => {
  let result = items.value
  if (filterLocation.value && filterLocation.value !== 'Tous') {
    result = result.filter(i => i.location === filterLocation.value)
  }
  return result
})

function showError(msg) {
  errorMsg.value = msg
  errorSnack.value = true
}

function showSuccess(msg) {
  successMsg.value = msg
  successSnack.value = true
}

async function load() {
  try {
    const [itemsRes, alertsRes, locRes] = await Promise.all([
      api.get('/inventory/'),
      api.get('/inventory/alerts'),
      api.get('/inventory/locations/summary'),
    ])
    items.value = itemsRes.data
    stockAlerts.value = alertsRes.data
    locationSummary.value = locRes.data
  } catch (e) {
    showError('Erreur de chargement de l\'inventaire')
    console.error('Inventory load error:', e)
  }
}

function openNewItem() {
  itemEditId.value = null
  itemForm.value = { ...defaultItemForm }
  nameSelect.value = null
  categorySelect.value = null
  locationSelect.value = null
  showItemForm.value = true
}

function editItem(item) {
  itemEditId.value = item.id
  itemForm.value = { ...item }
  // Pré-sélectionne la valeur existante dans la liste (ou « Nouveau… » si absente)
  nameSelect.value = item.name
    ? (names.value.includes(item.name) ? item.name : NEW_OPTION)
    : null
  categorySelect.value = item.category
    ? (categories.value.includes(item.category) ? item.category : NEW_OPTION)
    : null
  locationSelect.value = item.location
    ? (locations.value.includes(item.location) ? item.location : NEW_OPTION)
    : null
  showItemForm.value = true
}

async function saveItem() {
  if (!itemForm.value.name) { showError('Le nom est obligatoire'); return }
  saving.value = true
  try {
    if (itemEditId.value) {
      await api.put(`/inventory/${itemEditId.value}`, itemForm.value)
    } else {
      await api.post('/inventory/', itemForm.value)
    }
    showItemForm.value = false
    itemEditId.value = null
    showSuccess('Article enregistré')
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors de l\'enregistrement')
  } finally {
    saving.value = false
  }
}

async function deleteItem(id) {
  if (!confirm('Supprimer cet article ?')) return
  try {
    await api.delete(`/inventory/${id}`)
    showSuccess('Article supprimé')
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors de la suppression')
  }
}

function openMovement(item, type) {
  mvtItem.value = item
  mvtType.value = type
  mvtQty.value = 1
  mvtReason.value = ''
  showMvt.value = true
}

async function saveMovement() {
  if (mvtQty.value < 1) { showError('La quantité doit être au minimum 1'); return }
  saving.value = true
  try {
    await api.post('/inventory/movements', {
      item_id: mvtItem.value.id,
      movement_type: mvtType.value,
      quantity: mvtQty.value,
      reason: mvtReason.value,
    })
    showMvt.value = false
    showSuccess('Mouvement enregistré')
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors du mouvement')
  } finally {
    saving.value = false
  }
}

function openMove(item) {
  moveItem.value = item
  moveQty.value = item.quantity
  moveLocationSelect.value = null
  moveNewLocation.value = ''
  showMoveDialog.value = true
}

async function confirmMove() {
  const dest = (moveNewLocation.value || '').trim()
  if (!dest) { showError('Veuillez choisir ou saisir un emplacement'); return }
  if (dest === (moveItem.value.location || '')) { showError('L\'article est déjà à cet emplacement'); return }
  const qty = Number(moveQty.value)
  if (!qty || qty < 1) { showError('La quantité à déplacer doit être au minimum 1'); return }
  if (qty > moveItem.value.quantity) { showError('Quantité supérieure au stock disponible'); return }
  saving.value = true
  try {
    const partial = qty < moveItem.value.quantity
    await api.put(`/inventory/${moveItem.value.id}/move`, {
      new_location: dest,
      quantity: qty,
    })
    showMoveDialog.value = false
    showSuccess(partial
      ? `${qty} ${moveItem.value.unit} de « ${moveItem.value.name} » déplacé(s) vers ${dest}`
      : `« ${moveItem.value.name} » déplacé vers ${dest}`)
    await load()
  } catch (e) {
    showError(e.response?.data?.detail || 'Erreur lors du déplacement')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
