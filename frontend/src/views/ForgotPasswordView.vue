<template>
  <v-container class="fill-height login-page" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-6 pa-sm-8 login-card" :elevation="0">
          <div class="text-center mb-6">
            <v-avatar color="primary" size="60" variant="flat" class="login-badge">
              <v-icon size="32" color="white">mdi-lock-question</v-icon>
            </v-avatar>
            <h2 class="mt-4 mb-1">Mot de passe oublié</h2>
            <p class="text-body-2 r-muted">
              Nous vous envoyons un lien pour en choisir un nouveau.
            </p>
          </div>

          <!-- Une fois la demande partie, le formulaire n'a plus lieu d'être :
               le réafficher inciterait à renvoyer des demandes en boucle. -->
          <template v-if="sent">
            <v-alert type="success" variant="tonal" class="mb-4">
              {{ message }}
            </v-alert>
            <p class="text-body-2 r-muted mb-4">
              Le lien reste valable une heure et ne fonctionne qu'une seule fois.
            </p>
            <v-btn color="primary" block :to="{ name: 'login' }">Retour à la connexion</v-btn>
          </template>

          <v-form v-else @submit.prevent="submit">
            <v-text-field
              v-model="identifier"
              label="Identifiant ou adresse e-mail"
              prepend-inner-icon="mdi-account"
              autocapitalize="none"
              autocomplete="username"
              hint="Par exemple « paulin » ou votre adresse e-mail"
              persistent-hint
              class="mb-3"
              autofocus
            />
            <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
            <v-btn type="submit" color="primary" block size="large" :loading="loading">
              Envoyer le lien
            </v-btn>
            <v-btn variant="text" block class="mt-2" :to="{ name: 'login' }">
              Revenir à la connexion
            </v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import api from '../services/api'
import { apiError } from '../services/toast'

const identifier = ref('')
const loading = ref(false)
const error = ref('')
const sent = ref(false)
const message = ref('')

async function submit() {
  if (!identifier.value.trim()) {
    error.value = 'Indiquez votre identifiant ou votre adresse e-mail.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post('/users/password-reset/request', {
      identifier: identifier.value.trim(),
    })
    message.value = data.detail
    sent.value = true
  } catch (e) {
    error.value = apiError(e, "L'envoi a échoué. Réessayez dans un instant.")
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
