<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="pa-6" elevation="8">
          <div class="text-center mb-4">
            <v-icon size="64" color="primary">mdi-bee</v-icon>
            <h2 class="text-h5 mt-2">Rucher Manager</h2>
            <p class="text-body-2 text-grey">Connexion à votre espace</p>
          </div>
          <v-form @submit.prevent="doLogin">
            <v-text-field v-model="email" label="Email" type="email" prepend-inner-icon="mdi-email" required />
            <v-text-field v-model="password" label="Mot de passe" type="password" prepend-inner-icon="mdi-lock" required />
            <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
            <v-btn type="submit" color="primary" block size="large" :loading="loading">Se connecter</v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function doLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    // Attendre la fin de la navigation pour éviter toute redirection « redondante »
    const redirect = router.currentRoute.value.query.redirect
    await router.replace(typeof redirect === 'string' ? redirect : '/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>
