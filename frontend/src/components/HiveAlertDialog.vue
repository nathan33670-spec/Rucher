<template>
  <v-dialog v-model="open" max-width="560">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="error">mdi-alert-outline</v-icon>
        Signaler un problème
      </v-card-title>

      <v-card-text>
        <!-- Tout ne se passe pas dans une ruche : une clôture cassée ou un
             voisin mécontent n'a rien à faire dans l'historique d'une colonie. -->
        <v-btn-toggle
          v-model="mode" mandatory divided variant="outlined"
          color="error" class="d-flex mb-4"
        >
          <v-btn value="hive" class="flex-grow-1" prepend-icon="mdi-beehive-outline">
            Sur une ruche
          </v-btn>
          <v-btn value="general" class="flex-grow-1" prepend-icon="mdi-account-group">
            Général
          </v-btn>
        </v-btn-toggle>

        <!-- ── Signalement sur une ruche ── -->
        <template v-if="mode === 'hive'">
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
        </template>

        <!-- ── Signalement général ── -->
        <template v-else>
          <p class="text-body-2 r-muted mb-4">
            Pour ce qui ne concerne pas une colonie : clôture, accès, matériel
            commun, voisinage, point à passer au bureau. <b>Rien n'est écrit
            dans l'historique d'une ruche.</b>
          </p>

          <v-select
            v-model="apiaryId"
            :items="apiaryOptions"
            item-title="name"
            item-value="id"
            label="Rucher concerné (facultatif)"
            prepend-inner-icon="mdi-hexagon-multiple"
            :loading="loading"
            clearable
            hint="Laissez vide si le signalement concerne l'association en général."
            persistent-hint
            class="mb-2"
          />
        </template>

        <v-textarea
          v-model="message"
          label="Que se passe-t-il ?"
          :hint="mode === 'hive'
            ? 'ex. Ruche renversée, forte agressivité, entrée obstruée…'
            : 'ex. Clôture ouverte, chemin impraticable, enfumoir manquant…'"
          persistent-hint
          rows="4"
          maxlength="500"
          class="mt-2"
          :error-messages="messageError"
        />

        <v-alert v-if="destinataires" type="info" variant="tonal" density="compact" class="mt-4">
          {{ destinataires }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="open = false">Annuler</v-btn>
        <v-btn color="error" :loading="sending" prepend-icon="mdi-send" @click="send">
          {{ mode === 'hive' ? "Envoyer l'alerte" : 'Envoyer le signalement' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '../services/api'
import { toastError, toastSuccess, apiError } from '../services/toast'
import { hiveLabel } from '../services/hive'

const open = defineModel({ type: Boolean, default: false })

const mode = ref('hive')
const hives = ref([])
const apiaries = ref([])
const loading = ref(false)
const sending = ref(false)
const hiveId = ref(null)
const apiaryId = ref(null)
const message = ref('')
const hiveError = ref('')
const messageError = ref('')

const hiveOptions = computed(() =>
  hives.value.map((h) => ({
    id: h.id,
    label: [hiveLabel(h), h.apiary_name]
      .filter(Boolean)
      .join(' — '),
    managers: h.managers || [],
  })),
)

const apiaryOptions = computed(() => apiaries.value.map((a) => ({ id: a.id, name: a.name })))

// Rappel de qui sera prévenu : on n'envoie pas une alerte « dans le vide ».
const destinataires = computed(() => {
  if (mode.value === 'general') {
    const ou = apiaryId.value
      ? apiaries.value.find((a) => a.id === apiaryId.value)?.name
      : null
    return ou
      ? `Seront notifiés : les administrateurs, les responsables de rucher, et les responsables des ruches du rucher « ${ou} ».`
      : 'Seront notifiés : les administrateurs et les responsables de rucher.'
  }
  if (!hiveId.value) return ''
  const h = hives.value.find((x) => x.id === hiveId.value)
  const names = (h?.managers || []).map((m) => m.name).filter(Boolean)
  if (!names.length) {
    return "Aucun responsable désigné sur cette ruche : l'alerte partira aux adhérents abonnés aux alertes."
  }
  return 'Sera notifié : ' + names.join(', ') + '.'
})

async function loadData() {
  loading.value = true
  try {
    const [h, a] = await Promise.all([
      api.get('/apiaries/hives/all'),
      api.get('/apiaries/'),
    ])
    hives.value = h.data
    apiaries.value = a.data
  } catch (e) {
    toastError(apiError(e, 'Impossible de charger les ruchers et les ruches'))
  } finally {
    loading.value = false
  }
}

watch(hiveId, (v) => { if (v) hiveError.value = '' })
watch(message, (v) => { if (v && v.trim()) messageError.value = '' })
// Changer de type de signalement ne doit pas laisser traîner le reproche
// adressé à l'autre formulaire.
watch(mode, () => { hiveError.value = ''; messageError.value = '' })

watch(open, (v) => {
  if (!v) return
  mode.value = 'hive'
  hiveId.value = null
  apiaryId.value = null
  message.value = ''
  hiveError.value = ''
  messageError.value = ''
  if (!hives.value.length || !apiaries.value.length) loadData()
})

async function send() {
  const general = mode.value === 'general'
  hiveError.value = general || hiveId.value ? '' : 'Choisissez la ruche concernée.'
  messageError.value = message.value.trim() ? '' : 'Décrivez le problème en quelques mots.'
  if (hiveError.value || messageError.value) return

  sending.value = true
  try {
    if (general) {
      const { data } = await api.post('/notifications/report', {
        message: message.value.trim(),
        apiary_id: apiaryId.value ?? null,
      })
      toastSuccess(data.recipients
        ? `Signalement transmis à ${data.recipients} personne${data.recipients > 1 ? 's' : ''}`
        : 'Signalement transmis')
    } else {
      await api.post('/visits/alert', { hive_id: hiveId.value, message: message.value.trim() })
      toastSuccess('Alerte envoyée aux responsables de la ruche')
    }
    open.value = false
  } catch (e) {
    toastError(apiError(e, "Le signalement n'a pas pu être envoyé"))
  } finally {
    sending.value = false
  }
}
</script>
