<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Utilisateurs</h2>
      <div class="d-flex flex-wrap ga-2">
        <v-btn color="secondary" prepend-icon="mdi-upload" @click="csvInput.click()">Import CSV</v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openNewUser">Nouvel utilisateur</v-btn>
      </div>
    </div>
    <input ref="csvInput" type="file" accept=".csv" style="display:none" @change="importCSV" />

    <v-alert v-if="csvResult" :type="csvResult.errors?.length ? 'warning' : 'success'" closable @click:close="csvResult = null" class="mb-3">
      {{ csvResult.created }} utilisateurs importés.
      <div v-for="e in csvResult.errors" :key="e" class="text-caption">{{ e }}</div>
    </v-alert>

    <FilterBar
      v-model="filters" :fields="filterFields"
      :total="users.length" :shown="filteredUsers.length" item-label="compte"
    />

    <v-data-table :headers="headers" :items="filteredUsers" density="compact">
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
          <v-text-field v-model="form.email" label="Nom d'utilisateur" :disabled="!!formEditId" hint="Identifiant de connexion, sans e-mail (ex. paulin)" persistent-hint class="mb-2" />
          <v-text-field
            v-model="form.contact_email"
            label="Adresse e-mail"
            type="email"
            autocapitalize="none"
            prepend-inner-icon="mdi-email-outline"
            hint="Sert à joindre l'adhérent et à lui envoyer un lien de réinitialisation de mot de passe."
            persistent-hint
            :error-messages="emailError"
            class="mb-2"
          />
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
    <v-dialog v-model="showDelete" max-width="520">
      <v-card>
        <v-card-title>
          {{ delCheck && !delCheck.deletable ? 'Désactiver le compte' : "Supprimer l'utilisateur" }}
        </v-card-title>
        <v-card-text>
          <p class="mb-3">
            <b>{{ delUser?.first_name }} {{ delUser?.last_name }}</b>
            (<code>{{ delUser?.email }}</code>)
          </p>

          <div v-if="checkingDel" class="text-center py-4">
            <v-progress-circular indeterminate color="primary" size="26" />
          </div>

          <!-- Le compte a laissé une trace : on explique quoi, et on propose la
               seule action qui a du sens. -->
          <template v-else-if="delCheck && !delCheck.deletable">
            <v-alert type="info" variant="tonal" density="compact" class="mb-3">
              <div v-if="delCheck.blockers.length">
                Ce compte ne peut pas être supprimé : il a laissé
                <b>{{ blockersSentence }}</b>.
                Ces enregistrements font partie de l'historique de l'association
                et doivent conserver leur auteur.
              </div>
              <div v-for="(w, i) in delCheck.warnings" :key="i" :class="{ 'mt-2': delCheck.blockers.length || i }">
                {{ w }}
              </div>
            </v-alert>
            <p v-if="delCheck.is_active" class="text-body-2">
              En <b>désactivant</b> le compte, {{ delUser?.first_name }} ne pourra
              plus se connecter, mais tout son historique reste en place et
              conserve son nom.
            </p>
            <v-alert v-else type="success" variant="tonal" density="compact">
              Ce compte est déjà désactivé : il ne peut plus se connecter.
            </v-alert>
          </template>

          <template v-else-if="delCheck">
            <p>Ce compte n'a laissé aucun enregistrement : il peut être supprimé
              définitivement.</p>
            <v-alert
              v-for="(w, i) in delCheck.warnings" :key="i"
              type="warning" variant="tonal" density="compact" class="mt-3"
            >{{ w }}</v-alert>
            <p class="text-caption r-muted mt-2">Cette action est irréversible.</p>
          </template>

          <v-alert v-if="delError" type="error" density="compact" class="mt-3">{{ delError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showDelete = false">Annuler</v-btn>
          <v-btn
            v-if="delCheck && !delCheck.deletable && delCheck.is_active"
            color="warning" :loading="deleting" @click="deactivateUser"
          >
            Désactiver le compte
          </v-btn>
          <v-btn
            v-if="delCheck && delCheck.deletable"
            color="error" :loading="deleting" @click="confirmDelete"
          >
            Supprimer
          </v-btn>
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
import { ref, computed, watch, onMounted } from 'vue'
import FilterBar from '../components/FilterBar.vue'
import api from '../services/api'
import { toastError, toastSuccess, apiError } from '../services/toast'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref([])
const showForm = ref(false)
const formEditId = ref(null)
const form = ref({ email: '', contact_email: '', password: '', first_name: '', last_name: '', phone: '', roles: ['user'], is_active: true })
// Message d'unicité de l'adresse, affiché sous le champ concerné.
const emailError = ref('')
watch(() => form.value.contact_email, () => { emailError.value = '' })
const csvInput = ref(null)
const csvResult = ref(null)

const showPwDialog = ref(false)
const pwUser = ref(null)
const newPassword = ref('')

const showDelete = ref(false)
const delUser = ref(null)
const delError = ref('')
const deleting = ref(false)
const delCheck = ref(null)
const checkingDel = ref(false)
const blockersSentence = computed(() =>
  (delCheck.value?.blockers || []).map((b) => `${b.count} ${b.label}`).join(', '),
)

const roleOptions = [
  { title: 'Administrateur', value: 'admin' },
  { title: 'Trésorier', value: 'treasurer' },
  { title: 'Responsable rucher', value: 'yard_manager' },
  { title: 'Usager', value: 'user' },
  { title: 'Lecture seule', value: 'readonly' },
]

// ─── Filtres ──────────────────────────────────────────────
// Passé une dizaine d'adhérents, retrouver un compte demandait de parcourir
// les pages : la liste se filtre comme les autres écrans.
const filters = ref({ q: null, role: null, active: null })
const filterFields = computed(() => [
  { key: 'q', label: 'Nom, identifiant ou e-mail', type: 'search' },
  { key: 'role', label: 'Rôle', type: 'select', icon: 'mdi-shield-account-outline',
    items: roleOptions.map((r) => ({ title: r.title, value: r.value })) },
  { key: 'active', label: 'État', type: 'select', icon: 'mdi-account-check-outline',
    items: [{ title: 'Actifs', value: 'yes' }, { title: 'Désactivés', value: 'no' }] },
])

const filteredUsers = computed(() => {
  const f = filters.value
  const needle = (f.q || '').trim().toLowerCase()
  return users.value.filter((u) => {
    if (f.role && !(u.roles || []).includes(f.role)) return false
    if (f.active === 'yes' && !u.is_active) return false
    if (f.active === 'no' && u.is_active) return false
    if (needle) {
      const hay = `${u.first_name} ${u.last_name} ${u.email} ${u.contact_email || ''}`.toLowerCase()
      if (!hay.includes(needle)) return false
    }
    return true
  })
})

const headers = [
  { title: 'Nom', key: 'last_name' },
  { title: 'Prénom', key: 'first_name' },
  { title: 'Identifiant', key: 'email' },
  { title: 'Adresse e-mail', key: 'contact_email' },
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
    toastError(apiError(e, 'Chargement des utilisateurs impossible'))
  }
}

const EMPTY_USER = {
  email: '', contact_email: '', password: '', first_name: '', last_name: '',
  phone: '', roles: ['user'], is_active: true,
}

function openNewUser() {
  // Sans cette remise à zéro, le formulaire rouvrait avec les données du
  // dernier compte modifié — et l'on créait un doublon sans s'en apercevoir.
  formEditId.value = null
  form.value = { ...EMPTY_USER }
  emailError.value = ''
  showForm.value = true
}

function editUser(u) {
  formEditId.value = u.id
  form.value = { ...u, contact_email: u.contact_email || '', password: '' }
  emailError.value = ''
  showForm.value = true
}

async function saveUser() {
  emailError.value = ''
  if (!form.value.email?.trim()) { toastError("L'identifiant est obligatoire"); return }
  if (!form.value.first_name?.trim() || !form.value.last_name?.trim()) {
    toastError('Prénom et nom sont obligatoires'); return
  }
  if (!formEditId.value && (form.value.password || '').length < 6) {
    toastError('Le mot de passe doit faire au moins 6 caractères'); return
  }
  try {
    const payload = { ...form.value, contact_email: form.value.contact_email?.trim() || null }
    if (formEditId.value) {
      await api.put(`/users/${formEditId.value}`, payload)
    } else {
      await api.post('/users/', payload)
    }
    const wasEdit = !!formEditId.value
    showForm.value = false
    formEditId.value = null
    await load()
    toastSuccess(wasEdit ? 'Utilisateur modifié' : 'Utilisateur créé')
  } catch (e) {
    const msg = apiError(e, "Enregistrement impossible")
    // Adresse déjà utilisée : le message appartient au champ, pas au bandeau.
    if (e?.response?.status === 409) emailError.value = msg
    else toastError(msg)
  }
}

function resetPw(u) {
  pwUser.value = u
  newPassword.value = ''
  showPwDialog.value = true
}

async function confirmResetPw() {
  if (!newPassword.value || newPassword.value.length < 6) {
    toastError('Le mot de passe doit faire au moins 6 caractères')
    return
  }
  try {
    await api.put(`/users/${pwUser.value.id}/password`, { new_password: newPassword.value })
    showPwDialog.value = false
    // Le compte visé est déconnecté de tous ses appareils : il faut le dire.
    toastSuccess(`Mot de passe de ${pwUser.value.first_name} modifié — ce compte a été déconnecté de tous ses appareils`)
  } catch (e) {
    toastError(apiError(e, 'Erreur lors du changement de mot de passe'))
  }
}

async function askDelete(u) {
  delUser.value = u
  delError.value = ''
  delCheck.value = null
  showDelete.value = true
  // On demande au serveur ce qui retient le compte AVANT de proposer quoi que
  // ce soit : laisser cliquer sur « Supprimer » pour se heurter à une erreur de
  // contrainte n'apprend rien à personne.
  checkingDel.value = true
  try {
    const { data } = await api.get(`/users/${u.id}/deletion-check`)
    delCheck.value = data
  } catch (e) {
    delError.value = apiError(e, 'Vérification impossible')
  } finally {
    checkingDel.value = false
  }
}

/** Désactivation : la personne ne se connecte plus, son historique reste. */
async function deactivateUser() {
  deleting.value = true
  delError.value = ''
  try {
    await api.put(`/users/${delUser.value.id}`, { is_active: false })
    showDelete.value = false
    await load()
    toastSuccess(`${delUser.value.first_name} ne peut plus se connecter — son historique est conservé`)
  } catch (e) {
    delError.value = apiError(e, 'Désactivation impossible')
  } finally {
    deleting.value = false
  }
}

async function confirmDelete() {
  deleting.value = true
  delError.value = ''
  try {
    await api.delete(`/users/${delUser.value.id}`)
    showDelete.value = false
    await load()
    toastSuccess('Utilisateur supprimé')
  } catch (e) {
    delError.value = apiError(e, 'Suppression impossible')
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
