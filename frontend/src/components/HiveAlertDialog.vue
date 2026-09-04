<template>
  <v-dialog v-model="open" max-width="520">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="error">mdi-alert-outline</v-icon>
        Signaler un problème
      </v-card-title>

      <v-card-text>
        <p class="text-body-2 r-muted mb-4">
          Les responsables de la ruche reçoivent immédiatement une notification.
          Le signalement est ajouté à l'historique de la ruche.
        </p>

        <v-autocomplete
          v-model="hiveId"
          :items="hiveOptions"
          item-title="label"
          item-value="id"
          label="Ruche concernée"
          prepend-inner-icon="mdi-beehive-outline"
          :loading="loading"
          :error-messages="hiveError"
        />

        <v-textarea
          v-model="message"
          label="Que se passe-t-il ?"
          hint="ex. Ruche renversée, forte agressivité, entrée obstruée…"
          persistent-hint
          rows="4"
          maxlength="500"
          :error-messages="messageError"
        />

        <v-alert v-if="managersHint" type="info" variant="tonal" density="compact">
          {{ managersHint }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="open = false">Annuler</v-btn>
        <v-btn color="error" :loading="sending" prepend-icon="mdi-send" @click="send">
          Envoyer l'alerte
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '../services/api'
import { toastError, toastSuccess, apiError } from '../services/toast'

const open = defineModel({ type: Boolean, default: false })

const hives = ref([])
const loading = ref(false)
const sending = ref(false)
const hiveId = ref(null)
const message = ref('')
const hiveError = ref('')
const messageError = ref('')

const hiveOptions = computed(() =>
  hives.value.map((h) => ({
    id: h.id,
    label: [h.name || h.napi_number || `Ruche #${h.id}`, h.apiary_name]
      .filter(Boolean)
      .join(' — '),
    managers: h.managers || [],
  })),
)

// Rappel de qui sera prévenu : on n'envoie pas une alerte « dans le vide ».
const managersHint = computed(() => {
  if (!hiveId.value) return ''
  const h = hives.value.find((x) => x.id === hiveId.value)
  const names = (h?.managers || []).map((m) => m.name).filter(Boolean)
  if (!names.length) {
    return "Aucun responsable désigné sur cette ruche : l'alerte partira aux adhérents abonnés aux alertes."
  }
  return 'Sera notifié : ' + names.join(', ') + '.'
})

async function loadHives() {
  loading.value = true
  try {
    const { data } = await api.get('/apiaries/hives/all')
    hives.value = data
  } catch (e) {
    toastError(apiError(e, 'Impossible de charger la liste des ruches'))
  } finally {
    loading.value = false
  }
}

watch(hiveId, (v) => { if (v) hiveError.value = '' })
watch(message, (v) => { if (v && v.trim()) messageError.value = '' })

watch(open, (v) => {
  if (!v) return
  hiveId.value = null
  message.value = ''
  hiveError.value = ''
  messageError.value = ''
  if (!hives.value.length) loadHives()
})

async function send() {
  hiveError.value = hiveId.value ? '' : 'Choisissez la ruche concernée.'
  messageError.value = message.value.trim() ? '' : 'Décrivez le problème en quelques mots.'
  if (hiveError.value || messageError.value) return

  sending.value = true
  try {
    await api.post('/visits/alert', { hive_id: hiveId.value, message: message.value.trim() })
    toastSuccess('Alerte envoyée aux responsables de la ruche')
    open.value = false
  } catch (e) {
    toastError(apiError(e, "L'alerte n'a pas pu être envoyée"))
  } finally {
    sending.value = false
  }
}
</script>
