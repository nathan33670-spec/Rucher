<template>
  <v-app>
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
</script>
