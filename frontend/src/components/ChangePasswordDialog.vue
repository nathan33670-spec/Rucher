<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="440">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-lock-reset</v-icon> Changer mon mot de passe
      </v-card-title>
      <v-card-text>
        <v-form @submit.prevent="submit">
          <v-text-field v-model="current" label="Mot de passe actuel" type="password" autocomplete="current-password" prepend-inner-icon="mdi-lock" />
          <v-text-field v-model="next" label="Nouveau mot de passe" type="password" autocomplete="new-password" prepend-inner-icon="mdi-lock-plus" hint="6 caractères minimum" persistent-hint />
          <v-text-field v-model="confirm" label="Confirmer le nouveau mot de passe" type="password" autocomplete="new-password" prepend-inner-icon="mdi-lock-check" />
          <v-alert v-if="error" type="error" density="compact" class="mt-2">{{ error }}</v-alert>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="close">Annuler</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">Enregistrer</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'done'])
const auth = useAuthStore()

const current = ref('')
const next = ref('')
const confirm = ref('')
const error = ref('')
const saving = ref(false)

watch(() => props.modelValue, (v) => { if (v) reset() })

function reset() { current.value = ''; next.value = ''; confirm.value = ''; error.value = '' }
function close() { emit('update:modelValue', false) }

async function submit() {
  error.value = ''
  if (!current.value) { error.value = 'Saisissez votre mot de passe actuel'; return }
  if (next.value.length < 6) { error.value = 'Le nouveau mot de passe doit faire au moins 6 caractères'; return }
  if (next.value !== confirm.value) { error.value = 'Les deux mots de passe ne correspondent pas'; return }
  saving.value = true
  try {
    await auth.changeMyPassword(current.value, next.value)
    emit('done')
    close()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur lors du changement de mot de passe'
  } finally {
    saving.value = false
  }
}
</script>
