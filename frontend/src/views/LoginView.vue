<template>
  <v-container class="fill-height login-page" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="pa-6 pa-sm-8 login-card" :elevation="0">
          <div class="text-center mb-6">
            <v-avatar color="primary" size="60" variant="flat" class="login-badge">
              <v-icon size="32" color="white">mdi-bee</v-icon>
            </v-avatar>
            <h2 class="mt-4 mb-1">Rucher Manager</h2>
            <p class="text-body-2 r-muted">Connexion à votre espace</p>
          </div>
          <v-form @submit.prevent="doLogin">
            <v-text-field v-model="username" label="Nom d'utilisateur" type="text" autocapitalize="none" autocomplete="username" prepend-inner-icon="mdi-account" hint="Votre identifiant (ex. paulin)" required />
            <v-text-field v-model="password" label="Mot de passe" type="password" prepend-inner-icon="mdi-lock" autocomplete="current-password" required />
            <v-checkbox v-model="remember" color="primary" density="compact" hide-details class="mb-2">
              <template v-slot:label>
                <span class="text-body-2">Rester connecté sur cet appareil</span>
              </template>
            </v-checkbox>
            <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>
            <v-btn type="submit" color="primary" block size="large" class="mt-1" :loading="loading">
              Se connecter
            </v-btn>
          </v-form>

          <!-- Installation « comme une application » (mobile) -->
          <template v-if="canInstall">
            <v-divider class="my-5" />
            <p class="text-caption r-muted text-center mb-2">
              <v-icon size="16" class="mr-1">mdi-cellphone</v-icon>
              Installez Rucher sur votre téléphone pour l'utiliser hors-ligne
            </p>
            <InstallButton block label="Ajouter à l'écran d'accueil" />
          </template>

          <div class="text-center mt-5">
            <v-btn variant="text" size="small" :to="{ name: 'docs-home' }" prepend-icon="mdi-book-open-variant">
              Consulter la documentation
            </v-btn>
          </div>
        </v-card>

        <p class="text-center text-caption r-muted mt-4">
          Association apicole · Gestion des ruchers
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { canInstall } from '../services/pwa'
import InstallButton from '../components/InstallButton.vue'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const remember = ref(true)
const error = ref('')
const loading = ref(false)

async function doLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value, remember.value)
    // Attendre la fin de la navigation pour éviter toute redirection « redondante »
    const redirect = router.currentRoute.value.query.redirect
    await router.replace(typeof redirect === 'string' ? redirect : { name: 'dashboard' })
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Fond : dégradé chaud très doux + trame alvéolaire à peine perceptible.
   Uniquement en CSS — aucune image à télécharger. */
.login-page {
  position: relative;
  background:
    radial-gradient(ellipse 70% 60% at 15% -5%, rgba(198, 138, 18, 0.2), transparent 70%),
    radial-gradient(ellipse 60% 55% at 90% 105%, rgba(93, 64, 55, 0.12), transparent 70%),
    #FBF7F0;
}

/* Carte de connexion : ombre douce et large, filet très clair. */
.login-card {
  border-radius: 20px !important;
  box-shadow: 0 20px 48px rgba(74, 52, 26, 0.11), 0 2px 8px rgba(74, 52, 26, 0.05) !important;
  background-color: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(6px);
}

/* Pastille de l'abeille : léger halo miel. */
.login-badge {
  box-shadow: 0 0 0 6px rgba(198, 138, 18, 0.12);
}
</style>
