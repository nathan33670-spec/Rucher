<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Trésorerie</h2>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openNewTx">Nouvelle écriture</v-btn>
    </div>

    <!-- Résumé annuel — même traitement que les tuiles du tableau de bord -->
    <v-row dense class="mb-4">
      <v-col cols="12" sm="4">
        <v-card class="pa-4">
          <div class="d-flex align-center ga-3">
            <v-avatar color="success" variant="tonal" size="40" rounded="lg">
              <v-icon color="success" size="21">mdi-arrow-down-circle-outline</v-icon>
            </v-avatar>
            <div class="min-width-0">
              <div class="r-stat-value text-success">{{ money(summary.income) }}</div>
              <div class="r-stat-label">Recettes</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card class="pa-4">
          <div class="d-flex align-center ga-3">
            <v-avatar color="error" variant="tonal" size="40" rounded="lg">
              <v-icon color="error" size="21">mdi-arrow-up-circle-outline</v-icon>
            </v-avatar>
            <div class="min-width-0">
              <div class="r-stat-value text-error">{{ money(summary.expense) }}</div>
              <div class="r-stat-label">Dépenses</div>
            </div>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card class="pa-4 balance-card">
          <div class="d-flex align-center ga-3">
            <v-avatar :color="balanceColor" variant="tonal" size="40" rounded="lg">
              <v-icon :color="balanceColor" size="21">mdi-scale-balance</v-icon>
            </v-avatar>
            <div class="min-width-0">
              <div class="r-stat-value" :class="`text-${balanceColor}`">{{ money(summary.balance) }}</div>
              <div class="r-stat-label">Solde</div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <FilterBar
      v-model="filters" :fields="filterFields"
      :total="transactions.length" :shown="filteredTransactions.length" item-label="écriture"
    />

    <v-data-table :headers="headers" :items="filteredTransactions" density="compact">
      <template v-slot:item.transaction_type="{ item }">
        <v-chip :color="item.transaction_type === 'income' ? 'success' : 'error'" size="small">
          {{ item.transaction_type === 'income' ? 'Recette' : 'Dépense' }}
        </v-chip>
      </template>
      <template v-slot:item.category="{ item }">
        {{ categoryLabel(item.category) }}
      </template>
      <template v-slot:item.amount="{ item }">
        {{ money(item.amount) }}
      </template>
      <template v-slot:item.date="{ item }">
        {{ new Date(item.date).toLocaleDateString('fr-FR') }}
      </template>
      <template v-slot:item.supplier="{ item }">
        {{ item.supplier || '—' }}
      </template>
      <template v-slot:item.invoices="{ item }">
        <v-chip
          v-for="inv in item.invoices" :key="inv.id"
          size="x-small" class="mr-1" variant="tonal" color="primary"
          @click="downloadInvoice(inv.id, inv.filename)"
        >
          <v-icon start size="12">mdi-paperclip</v-icon>{{ inv.filename }}
        </v-chip>
        <v-btn icon size="x-small" variant="text" @click="uploadInvoice(item.id)" title="Joindre facture">
          <v-icon size="16">mdi-paperclip</v-icon>
        </v-btn>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn icon size="small" variant="text" @click="editTx(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn icon size="small" variant="text" @click="deleteTx(item.id)"><v-icon color="error">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Dialog écriture -->
    <v-dialog v-model="showForm" max-width="550">
      <v-card>
        <v-card-title>{{ editId ? 'Modifier' : 'Nouvelle' }} écriture</v-card-title>
        <v-card-text>
          <v-select v-model="form.transaction_type" :items="[{title:'Recette',value:'income'},{title:'Dépense',value:'expense'}]" label="Type" />
          <v-select v-model="form.category" :items="categories" item-title="title" item-value="value" label="Catégorie" />
          <v-text-field v-model.number="form.amount" label="Montant (€)" type="number" step="0.01" />
          <v-text-field v-model="form.supplier" label="Fournisseur" placeholder="(optionnel)" />
          <v-textarea v-model="form.description" label="Description" rows="2" />
          <!-- Upload facture direct à la création -->
          <v-file-input
            v-model="form.invoice_file"
            label="Joindre une facture (optionnel)"
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            prepend-icon="mdi-file-document"
            density="compact"
            clearable
            hide-details
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showForm = false">Annuler</v-btn>
          <v-btn color="primary" :loading="saving" @click="saveTx">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Upload facture (input caché pour les tx existantes) -->
    <input ref="fileInput" type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" style="display:none" @change="onFileSelected" />

    <v-snackbar v-model="errorSnack" color="error" timeout="4000">{{ errorMsg }}</v-snackbar>
    <v-snackbar v-model="successSnack" color="success" timeout="2000">{{ successMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FilterBar from '../components/FilterBar.vue'
import { apiError } from '../services/toast'
import api from '../services/api'
import { money } from '../services/format'
import { confirmAction } from '../services/confirm'

const transactions = ref([])
const summary = ref({ income: 0, expense: 0, balance: 0 })
// Solde positif → vert, négatif → rouge.
const balanceColor = computed(() => (summary.value.balance >= 0 ? 'success' : 'error'))
const showForm = ref(false)
const editId = ref(null)
const saving = ref(false)
const errorSnack = ref(false)
const errorMsg = ref('')
const successSnack = ref(false)
const successMsg = ref('')

const defaultForm = { transaction_type: 'expense', category: 'other', amount: 0, description: '', supplier: '', invoice_file: null }
const form = ref({ ...defaultForm })
const fileInput = ref(null)
const uploadTxId = ref(null)

const categories = [
  { title: 'Matériel', value: 'material' },
  { title: 'Traitement sanitaire', value: 'treatment' },
  { title: 'Vente de miel', value: 'honey_sale' },
  { title: 'Cotisations', value: 'membership' },
  { title: 'Autre', value: 'other' },
]

function categoryLabel(val) {
  const found = categories.find(c => c.value === val)
  return found ? found.title : val
}

// ─── Filtres ──────────────────────────────────────────────
// Retrouver « toutes les dépenses de matériel de mai » demandait de faire
// défiler toute l'année : le tri seul ne suffisait pas.
const filters = ref({ type: null, category: null, from: null, to: null, q: null })
const uniqTx = (l) => [...new Set(l.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b)))

const filterFields = computed(() => [
  { key: 'type', label: 'Sens', type: 'select', icon: 'mdi-swap-vertical',
    items: [{ title: 'Recettes', value: 'income' }, { title: 'Dépenses', value: 'expense' }] },
  { key: 'category', label: 'Catégorie', type: 'select', icon: 'mdi-tag-outline',
    items: uniqTx(transactions.value.map((t) => t.category)).map((c) => ({ title: c, value: c })) },
  { key: 'q', label: 'Libellé ou fournisseur', type: 'search' },
  { key: 'from', label: 'Du', type: 'date' },
  { key: 'to', label: 'Au', type: 'date' },
])

const filteredTransactions = computed(() => {
  const f = filters.value
  const needle = (f.q || '').trim().toLowerCase()
  return transactions.value.filter((t) => {
    if (f.type && t.transaction_type !== f.type) return false
    if (f.category && t.category !== f.category) return false
    if (needle && !`${t.description || ''} ${t.supplier || ''}`.toLowerCase().includes(needle)) return false
    const d = (t.date || '').substring(0, 10)
    if (f.from && d < f.from) return false
    if (f.to && d > f.to) return false
    return true
  })
})

const headers = [
  { title: 'Date', key: 'date' },
  { title: 'Type', key: 'transaction_type' },
  { title: 'Catégorie', key: 'category' },
  { title: 'Fournisseur', key: 'supplier' },
  { title: 'Montant', key: 'amount' },
  { title: 'Description', key: 'description' },
  { title: 'Factures', key: 'invoices', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false },
]

function showError(msg) { errorMsg.value = msg; errorSnack.value = true }
function showSuccess(msg) { successMsg.value = msg; successSnack.value = true }

async function load() {
  try {
    const [txRes, sumRes] = await Promise.all([
      api.get('/treasury/'),
      api.get('/treasury/summary'),
    ])
    transactions.value = txRes.data
    summary.value = sumRes.data
  } catch (e) {
    showError(apiError(e, 'Chargement de la trésorerie impossible'))
    console.error('Treasury load error:', e)
  }
}

function openNewTx() {
  editId.value = null
  form.value = { ...defaultForm, invoice_file: null }
  showForm.value = true
}

function editTx(t) {
  editId.value = t.id
  form.value = {
    transaction_type: t.transaction_type,
    category: t.category,
    amount: t.amount,
    description: t.description || '',
    supplier: t.supplier || '',
    invoice_file: null,
  }
  showForm.value = true
}

async function saveTx() {
  if (!form.value.amount || form.value.amount <= 0) {
    showError('Le montant doit être supérieur à 0')
    return
  }
  saving.value = true
  try {
    const payload = {
      transaction_type: form.value.transaction_type,
      category: form.value.category,
      amount: form.value.amount,
      description: form.value.description || null,
      supplier: form.value.supplier || null,
    }

    let txId
    if (editId.value) {
      await api.put('/treasury/' + editId.value, payload)
      txId = editId.value
    } else {
      const res = await api.post('/treasury/', payload)
      txId = res.data.id
    }

    // Upload facture si fichier sélectionné
    if (form.value.invoice_file) {
      const fd = new FormData()
      fd.append('file', form.value.invoice_file)
      await api.post('/treasury/' + txId + '/invoices', fd)
    }

    showForm.value = false
    editId.value = null
    showSuccess('Écriture enregistrée')
    await load()
  } catch (e) {
    showError(apiError(e, "Erreur lors de l'enregistrement"))
  } finally {
    saving.value = false
  }
}

async function deleteTx(id) {
  if (!(await confirmAction('Supprimer cette écriture ?'))) return
  try {
    await api.delete('/treasury/' + id)
    showSuccess('Écriture supprimée')
    await load()
  } catch (e) {
    showError(apiError(e, 'Erreur lors de la suppression'))
  }
}

function uploadInvoice(txId) {
  uploadTxId.value = txId
  fileInput.value.click()
}

async function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file || !uploadTxId.value) return
  try {
    const fd = new FormData()
    fd.append('file', file)
    await api.post('/treasury/' + uploadTxId.value + '/invoices', fd)
    showSuccess('Facture jointe')
    await load()
  } catch (err) {
    showError("Erreur lors de l'envoi de la facture")
  }
  fileInput.value.value = ''
}

async function downloadInvoice(invoiceId, filename) {
  try {
    const res = await api.get('/treasury/invoices/' + invoiceId + '/download', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    showError(apiError(e, 'Téléchargement impossible'))
  }
}

onMounted(load)
</script>

<style scoped>
.min-width-0 {
  min-width: 0;
}

/* Le solde porte l'information principale : filet légèrement plus marqué. */
.balance-card {
  border-color: rgba(93, 64, 55, 0.24) !important;
}
</style>
