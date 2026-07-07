<template>
  <v-dialog v-model="s.open" max-width="420" @update:model-value="(v) => { if (!v) resolve(false) }">
    <v-card>
      <v-card-title class="text-wrap">{{ s.title }}</v-card-title>
      <v-card-text>{{ s.message }}</v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="resolve(false)">Annuler</v-btn>
        <v-btn :color="s.color" variant="flat" @click="resolve(true)">{{ s.confirmText }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { confirmState as s, resolveConfirm as resolve } from '../services/confirm'
</script>
