<template>
  <v-dialog v-model="open" max-width="460">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-account-edit-outline</v-icon>
        Mes coordonnées
      </v-card-title>
      <v-card-text>
        <v-text-field
          :model-value="auth.user?.email"
          label="Identifiant de connexion"
          prepend-inner-icon="mdi-account"
          disabled
          hint="Il est fixé par l'administrateur."
          persistent-hint
          class="mb-3"
        />
        <v-text-field
          v-model="contactEmail"
          label="Adresse e-mail"
          type="email"
          autocapitalize="none"
          autocomplete="email"
          prepend-inner-icon="mdi-email-outline"
          hint="Indispensable pour réinitialiser vous-même votre mot de passe."
          persistent-hint
          :error-messages="emailError"
          class="mb-3"
        />
        <v-text-field
          v-model="phone"
          label="Téléphone"
          type="tel"
          autocomplete="tel"
          prepend-inner-icon="mdi-phone-outline"
        />
        <v-alert
          v-if="!contactEmail"
          type="warning" variant="tonal" density="compact" class="mt-3"
        >
          <span class="text-caption">
            Sans adresse e-mail, vous devrez passer par un administrateur si
            vous oubliez votre mot de passe.
          </span>
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="open = false">Annuler</v-btn>
        <v-btn color="primary" :loading="saving" @click="save">Enregistrer</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'
import { toastSuccess, apiError } from '../services/toast'

const open = defineModel({ type: Boolean, default: false })
const auth = useAuthStore()

const contactEmail = ref('')
const phone = ref('')
const emailError = ref('')
const saving = ref(false)

watch(open, (v) => {
  if (!v) return
  contactEmail.value = auth.user?.contact_email || ''
  phone.value = auth.user?.phone || ''
  emailError.value = ''
})
watch(contactEmail, () => { emailError.value = '' })

async function save() {
  saving.value = true
  emailError.value = ''
  try {
    await api.put('/users/me/profile', {
      contact_email: contactEmail.value.trim() || null,
      phone: phone.value.trim() || null,
    })
    await auth.fetchUser()
    toastSuccess('Coordonnées enregistrées')
    open.value = false
  } catch (e) {
    const msg = apiError(e, 'Enregistrement impossible')
    // Adresse déjà prise ou mal formée : le message appartient au champ.
    if (e?.response?.status === 409 || e?.response?.status === 422) emailError.value = msg
    else emailError.value = msg
  } finally {
    saving.value = false
  }
}
</script>
