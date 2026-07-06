<template>
  <template v-if="canInstall">
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

    <!-- Instructions d'installation (si l'invite native n'est pas disponible) -->
    <v-dialog v-model="showHelp" max-width="460">
      <v-card>
        <v-card-title class="text-wrap">📲 Installer l'application</v-card-title>
        <v-card-text>
          <template v-if="isIOS">
            <p class="mb-3">Sur iPhone / iPad, avec <b>Safari</b> :</p>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-export-variant">1. Touchez le bouton <b>Partager</b> (en bas).</v-list-item>
              <v-list-item prepend-icon="mdi-plus-box-outline">2. Choisissez <b>« Sur l'écran d'accueil »</b>.</v-list-item>
              <v-list-item prepend-icon="mdi-check">3. Validez : l'icône 🐝 apparaît.</v-list-item>
            </v-list>
          </template>
          <template v-else>
            <p class="mb-3">Sur Android (<b>Chrome</b>) ou ordinateur :</p>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-dots-vertical">1. Ouvrez le menu <b>⋮</b> du navigateur (en haut à droite).</v-list-item>
              <v-list-item prepend-icon="mdi-cellphone-arrow-down">2. Touchez <b>« Installer l'application »</b> ou <b>« Ajouter à l'écran d'accueil »</b>.</v-list-item>
              <v-list-item prepend-icon="mdi-check">3. Confirmez.</v-list-item>
            </v-list>
            <v-alert type="info" variant="tonal" density="compact" class="mt-2">
              L'option apparaît après quelques secondes de navigation. Si vous ne
              la voyez pas, rechargez la page et réessayez.
            </v-alert>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showHelp = false">Compris</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>
</template>

<script setup>
import { ref } from 'vue'
import { canInstall, isIOS, promptInstall, deferredPrompt } from '../services/pwa'

defineProps({
  block: { type: Boolean, default: false },
  label: { type: String, default: 'Installer l\'app' },
})

const showHelp = ref(false)

async function onClick() {
  // Invite native si disponible, sinon instructions manuelles.
  if (deferredPrompt.value) {
    const ok = await promptInstall()
    if (ok) return
    // refus ou indisponible → on montre quand même l'aide
    showHelp.value = true
  } else {
    showHelp.value = true
  }
}
</script>
