<template>
  <v-snackbar
    v-model="toastState.open"
    :color="toastState.color"
    :timeout="toastState.timeout"
    location="top"
  >
    {{ toastState.message }}
    <template v-slot:actions>
      <v-btn icon size="small" variant="text" @click="toastState.open = false">
        <v-icon size="18">mdi-close</v-icon>
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { toastState } from '../services/toast'
</script>
