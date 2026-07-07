<template>
  <v-app>
    <router-view />
    <!-- Boîte de confirmation globale (suppressions, etc.) -->
    <ConfirmDialog />
  </v-app>
</template>

<script setup>
// App root — le layout est géré par MainLayout.vue
import ConfirmDialog from './components/ConfirmDialog.vue'
</script>
