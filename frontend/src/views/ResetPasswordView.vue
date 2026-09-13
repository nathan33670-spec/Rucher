<template>
  <v-container class="fill-height login-page" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-6 pa-sm-8 login-card" :elevation="0">
          <div class="text-center mb-6">
            <v-avatar color="primary" size="60" variant="flat" class="login-badge">
              <v-icon size="32" color="white">mdi-lock-reset</v-icon>
            </v-avatar>
            <h2 class="mt-4 mb-1">Nouveau mot de passe</h2>
          </div>

          <div v-if="checking" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" />
          </div>

          <!-- Lien périmé : on le dit avant de faire saisir quoi que ce soit. -->
          <template v-else-if="!valid">
            <v-alert type="error" variant="tonal" class="mb-4">
              Ce lien n'est plus valable : il a expiré ou a déjà été utilisé.
            </v-alert>
            <v-btn color="primary" block :to="{ name: 'forgot-password' }">
              Demander un nouveau lien
            </v-btn>
            <v-btn variant="text" block class="mt-2" :to="{ name: 'login' }">
              Revenir à la connexion
            </v-btn>
          </template>

          <v-form v-else @submit.prevent="submit">
            <v-text-field
              v-model="password"
              label="Nouveau mot de passe"
              :type="show ? 'text' : 'password'"
              :append-inner-icon="show ? 'mdi-eye-off' : 'mdi-eye'"
              prepend-inner-icon="mdi-lock"
              autocomplete="new-password"
              hint="6 caractères minimum"
              persistent-hint
              class="mb-3"
              autofocus
              @click:append-inner="show = !show"
            />
            <v-text-field
              v-model="confirm"
              label="Confirmer le mot de passe"
              :type="show ? 'text' : 'password'"
              prepend-inner-icon="mdi-lock-check"
              autocomplete="new-password"
              :error-messages="mismatch ? 'Les deux saisies diffèrent.' : ''"
              class="mb-2"
            />
            <v-alert type="info" variant="tonal" density="compact" class="mb-3">
              <span class="text-caption">
                Vous serez déconnecté de tous vos autres appareils.
              </span>
            </v-alert>
            <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
            <v-btn type="submit" color="primary" block size="large" :loading="loading">
              Enregistrer et me connecter
            </v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'
import { apiError, toastSuccess } from '../services/toast'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const token = String(route.query.token || '')
const checking = ref(true)
const valid = ref(false)
const password = ref('')
const confirm = ref('')
const show = ref(false)
const loading = ref(false)
const error = ref('')

const mismatch = computed(() => !!confirm.value && password.value !== confirm.value)

// Le reproche disparaît dès qu'on corrige : le laisser affiché sous un
// formulaire déjà corrigé fait douter de ce qui bloque.
watch([password, confirm], () => { if (error.value) error.value = '' })

onMounted(async () => {
  if (!token) { checking.value = false; return }
  try {
    const { data } = await api.get('/users/password-reset/check', { params: { token } })
    valid.value = !!data.valid
  } catch {
    valid.value = false
  } finally {
    checking.value = false
  }
})

async function submit() {
  error.value = ''
  if (password.value.length < 6) {
    error.value = 'Le mot de passe doit faire au moins 6 caractères.'
    return
  }
  if (password.value !== confirm.value) {
    error.value = 'Les deux saisies diffèrent.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/users/password-reset/confirm', {
      token, new_password: password.value,
    })
    // Le serveur renvoie un jeton : l'adhérent vient de prouver l'accès à sa
    // boîte mail, le renvoyer saisir ce qu'il vient de choisir n'apporte rien.
    await auth.adoptToken(data.access_token)
    toastSuccess('Mot de passe enregistré')
    router.push({ name: 'dashboard' })
  } catch (e) {
    error.value = apiError(e, "La réinitialisation a échoué.")
    // Lien consommé entre-temps : inutile de laisser le formulaire.
    if (e?.response?.status === 400) valid.value = false
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { background: transparent; }
.login-card { border: 1px solid rgba(0, 0, 0, 0.06); border-radius: 16px; }
.login-badge { box-shadow: 0 6px 18px rgba(184, 134, 11, 0.28); }
</style>
