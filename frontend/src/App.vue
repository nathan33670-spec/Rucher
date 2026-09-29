<template>
  <v-app>
    <!-- Démonstration publique uniquement : absent du paquet de production. -->
    <DemoBanner v-if="MODE_DEMO" />
    <router-view />
    <!-- Boîte de confirmation globale (suppressions, etc.) -->
    <ConfirmDialog />
    <!-- Messages transitoires globaux (succès / erreurs) -->
    <AppToast />
  </v-app>
</template>

<script setup>
// App root — le layout est géré par MainLayout.vue
import ConfirmDialog from './components/ConfirmDialog.vue'
import AppToast from './components/AppToast.vue'
import DemoBanner from './components/DemoBanner.vue'
import { MODE_DEMO } from './services/api'
</script>
