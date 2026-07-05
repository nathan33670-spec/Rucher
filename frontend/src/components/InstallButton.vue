<template>
  <template v-if="canInstall">
    <!-- Bouton compact (barre d'app) ou bloc (page de connexion) -->
    <v-btn
      :block="block"
      :size="block ? 'large' : 'small'"
      :variant="block ? 'flat' : 'text'"
      :color="block ? 'primary' : undefined"
      prepend-icon="mdi-cellphone-arrow-down"
      @click="onClick"
    >
      {{ label }}
    </v-btn>

    <!-- Instructions iOS (pas d'invite native possible) -->
    <v-dialog v-model="showIos" max-width="420">
      <v-card>
        <v-card-title class="text-wrap">📲 Installer sur votre iPhone</v-card-title>
        <v-card-text>
          <p class="mb-3">Pour utiliser Rucher comme une application :</p>
          <v-list density="compact">
            <v-list-item prepend-icon="mdi-export-variant">
              1. Touchez le bouton <b>Partager</b> en bas de Safari.
            </v-list-item>
            <v-list-item prepend-icon="mdi-plus-box-outline">
              2. Choisissez <b>« Sur l'écran d'accueil »</b>.
            </v-list-item>
            <v-list-item prepend-icon="mdi-check">
              3. Validez : l'icône 🐝 apparaît sur votre écran.
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showIos = false">Compris</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>
</template>

<script setup>
import { ref } from 'vue'
import { canInstall, isIOS, promptInstall } from '../services/pwa'

defineProps({
  block: { type: Boolean, default: false },
  label: { type: String, default: 'Installer l\'app' },
})

const showIos = ref(false)

async function onClick() {
  if (isIOS) {
    showIos.value = true
  } else {
    await promptInstall()
  }
}
</script>
