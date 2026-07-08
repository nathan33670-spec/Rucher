<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Utilisateurs</h2>
      <div class="d-flex flex-wrap ga-2">
        <v-btn color="secondary" prepend-icon="mdi-upload" @click="csvInput.click()">Import CSV</v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="showForm = true">Nouvel utilisateur</v-btn>
      </div>
    </div>
    <input ref="csvInput" type="file" accept=".csv" style="display:none" @change="importCSV" />

    <v-alert v-if="csvResult" :type="csvResult.errors?.length ? 'warning' : 'success'" closable @click:close="csvResult = null" class="mb-3">
      {{ csvResult.created }} utilisateurs importés.
      <div v-for="e in csvResult.errors" :key="e" class="text-caption">{{ e }}</div>
    </v-alert>

    <v-data-table :headers="headers" :items="users" density="compact">
      <template v-slot:item.roles="{ item }">
        <v-chip v-for="r in item.roles" :key="r" size="x-small" class="mr-1" color="primary" variant="tonal">{{ roleLabel(r) }}</v-chip>
      </template>
      <template v-slot:item.is_active="{ item }">
        <v-icon :color="item.is_active ? 'success' : 'error'">{{ item.is_active ? 'mdi-check' : 'mdi-close' }}</v-icon>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn icon size="small" variant="text" @click="editUser(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn icon size="small" variant="text" @click="resetPw(item)"><v-icon>mdi-lock-reset</v-icon></v-btn>
        <v-btn v-if="item.id !== auth.user?.id" icon size="small" variant="text" color="error" @click="askDelete(item)"><v-icon>mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <!-- Dialog utilisateur -->
    <v-dialog v-model="showForm" max-width="500">
      <v-card>
        <v-card-title>{{ formEditId ? 'Modifier' : 'Nouvel' }} utilisateur</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.email" label="Nom d'utilisateur" :disabled="!!formEditId" hint="Identifiant de connexion, sans e-mail (ex. paulin)" persistent-hint />
          <v-text-field v-if="!formEditId" v-model="form.password" label="Mot de passe" type="password" />
          <v-row>
            <v-col><v-text-field v-model="form.first_name" label="Prénom" /></v-col>
            <v-col><v-text-field v-model="form.last_name" label="Nom" /></v-col>
          </v-row>
          <v-text-field v-model="form.phone" label="Téléphone" />
          <v-select v-model="form.roles" :items="roleOptions" item-title="title" item-value="value" label="Rôles" multiple chips />
          <v-switch v-if="formEditId" v-model="form.is_active" label="Actif" color="success" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showForm = false">Annuler</v-btn>
          <v-btn color="primary" @click="saveUser">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog suppression -->
    <v-dialog v-model="showDelete" max-width="440">
      <v-card>
        <v-card-title>Supprimer l'utilisateur</v-card-title>
        <v-card-text>
          <p>Supprimer définitivement <b>{{ delUser?.first_name }} {{ delUser?.last_name }}</b>
          (<code>{{ delUser?.email }}</code>) ?</p>
          <p class="text-caption text-grey mt-1">Cette action est irréversible.</p>
          <v-alert v-if="delError" type="error" density="compact" class="mt-3">{{ delError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showDelete = false">Annuler</v-btn>
          <v-btn color="error" :loading="deleting" @click="confirmDelete">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog reset password -->
    <v-dialog v-model="showPwDialog" max-width="400">
      <v-card>
        <v-card-title>Modifier le mot de passe</v-card-title>
        <v-card-text>
          <p class="mb-2">Utilisateur : <b>{{ pwUser?.first_name }} {{ pwUser?.last_name }}</b> (<code>{{ pwUser?.email }}</code>)</p>
          <v-text-field v-model="newPassword" label="Nouveau mot de passe" type="password" autocomplete="new-password" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showPwDialog = false">Annuler</v-btn>
          <v-btn color="primary" @click="confirmResetPw">Valider</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref([])
const showForm = ref(false)
const formEditId = ref(null)
const form = ref({ email: '', password: '', first_name: '', last_name: '', phone: '', roles: ['user'], is_active: true })
const csvInput = ref(null)
const csvResult = ref(null)

const showPwDialog = ref(false)
const pwUser = ref(null)
const newPassword = ref('')

const showDelete = ref(false)
const delUser = ref(null)
const delError = ref('')
const deleting = ref(false)

const roleOptions = [
  { title: 'Administrateur', value: 'admin' },
  { title: 'Trésorier', value: 'treasurer' },
  { title: 'Responsable rucher', value: 'yard_manager' },
  { title: 'Usager', value: 'user' },
  { title: 'Lecture seule', value: 'readonly' },
]

const headers = [
  { title: 'Nom', key: 'last_name' },
  { title: 'Prénom', key: 'first_name' },
  { title: 'Identifiant', key: 'email' },
  { title: 'Rôles', key: 'roles', sortable: false },
  { title: 'Actif', key: 'is_active' },
  { title: 'Actions', key: 'actions', sortable: false },
]

function roleLabel(r) {
  return { admin: 'Admin', treasurer: 'Trésorier', yard_manager: 'Resp. rucher', user: 'Usager', readonly: 'Lecture' }[r] || r
}

async function load() {
  try {
    const { data } = await api.get('/users/')
    users.value = data
  } catch (e) {
    console.error('Users load error:', e)
  }
}

function editUser(u) {
  formEditId.value = u.id
  form.value = { ...u, password: '' }
  showForm.value = true
}

async function saveUser() {
  try {
    if (formEditId.value) {
      await api.put(`/users/${formEditId.value}`, form.value)
    } else {
      await api.post('/users/', form.value)
    }
    showForm.value = false
    formEditId.value = null
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Erreur lors de l\'enregistrement')
  }
}

function resetPw(u) {
  pwUser.value = u
  newPassword.value = ''
  showPwDialog.value = true
}

async function confirmResetPw() {
  if (!newPassword.value || newPassword.value.length < 6) {
    alert('Le mot de passe doit faire au moins 6 caractères')
    return
  }
  try {
    await api.put(`/users/${pwUser.value.id}/password`, { new_password: newPassword.value })
    showPwDialog.value = false
  } catch (e) {
    alert(e.response?.data?.detail || 'Erreur lors du changement de mot de passe')
  }
}

function askDelete(u) {
  delUser.value = u
  delError.value = ''
  showDelete.value = true
}

async function confirmDelete() {
  deleting.value = true
  delError.value = ''
  try {
    await api.delete(`/users/${delUser.value.id}`)
    showDelete.value = false
    await load()
  } catch (e) {
    delError.value = e.response?.data?.detail || 'Erreur lors de la suppression'
  } finally {
    deleting.value = false
  }
}

async function importCSV(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await api.post('/users/import-csv', fd)
  csvResult.value = data
  csvInput.value.value = ''
  await load()
}

onMounted(load)
</script>
