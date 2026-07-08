<template>
  <div>
    <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-4">
      <h2>Événements</h2>
      <v-btn v-if="auth.isAdmin" color="primary" prepend-icon="mdi-calendar-plus" @click="openCreate">
        Nouvel événement
      </v-btn>
    </div>

    <div v-if="loading" class="text-center pa-8"><v-progress-circular indeterminate color="primary" /></div>

    <!-- État vide -->
    <v-card v-else-if="!events.length" variant="tonal" class="text-center pa-8">
      <v-icon size="64" color="primary" class="mb-3">mdi-calendar-blank</v-icon>
      <h3 class="text-h6 mb-1">Aucun événement pour le moment</h3>
      <p class="text-medium-emphasis mb-0">
        {{ auth.isAdmin ? 'Créez un événement pour prévenir les adhérents.' : 'Les événements de l\'association apparaîtront ici.' }}
      </p>
    </v-card>

    <template v-else>
      <template v-if="upcoming.length">
        <div class="text-overline text-primary mt-2 mb-1">À venir</div>
        <EventCardList :events="upcoming" @rsvp="doRsvp" @edit="openEdit" @remove="removeEvent" @participants="openParticipants" @calendar-ics="downloadICS" @calendar-google="openGoogle" :is-admin="auth.isAdmin" :busy-id="busyId" />
      </template>

      <template v-if="past.length">
        <div class="text-overline text-medium-emphasis mt-4 mb-1">Passés</div>
        <EventCardList :events="past" past @rsvp="doRsvp" @edit="openEdit" @remove="removeEvent" @participants="openParticipants" @calendar-ics="downloadICS" @calendar-google="openGoogle" :is-admin="auth.isAdmin" :busy-id="busyId" />
      </template>
    </template>

    <!-- Dialog création / édition (admin) -->
    <v-dialog v-model="showForm" max-width="560">
      <v-card>
        <v-card-title>{{ editId ? 'Modifier l\'événement' : 'Nouvel événement' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.title" label="Titre *" placeholder="ex: Visite du rucher de Bois-d'Arcy" />
          <v-text-field v-model="form.location" label="Lieu" placeholder="ex: Rucher de Bois-d'Arcy" prepend-inner-icon="mdi-map-marker" />
          <v-row>
            <v-col cols="12" sm="6"><v-text-field v-model="form.start_at" label="Début *" type="datetime-local" /></v-col>
            <v-col cols="12" sm="6"><v-text-field v-model="form.end_at" label="Fin" type="datetime-local" /></v-col>
          </v-row>
          <v-textarea v-model="form.description" label="Description" rows="3" placeholder="Détails, matériel à prévoir…" />
          <v-switch v-model="form.is_public" color="primary" hide-details inset
            :label="form.is_public ? 'Public — visible par tous les adhérents' : 'Privé — visible par les admins seulement'" />
          <v-checkbox v-if="!editId" v-model="form.notify" color="primary" hide-details
            :disabled="!form.is_public"
            label="Notifier tous les adhérents (notification sur leur téléphone)" />
          <p v-if="!editId && form.notify && form.is_public" class="text-caption text-medium-emphasis mt-1">
            Seuls les adhérents ayant activé les notifications recevront l'alerte.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showForm = false">Annuler</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog participants (admin) -->
    <v-dialog v-model="showParticipants" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-account-group</v-icon> Participants
          <v-spacer />
          <v-btn icon size="small" variant="text" @click="showParticipants = false"><v-icon>mdi-close</v-icon></v-btn>
        </v-card-title>
        <v-card-text>
          <div v-if="participants.length === 0" class="text-center text-medium-emphasis py-6">
            Personne n'a encore répondu.
          </div>
          <template v-else>
            <div v-for="grp in participantGroups" :key="grp.key">
              <template v-if="grp.items.length">
                <div class="d-flex align-center ga-2 mt-2 mb-1">
                  <v-icon :color="grp.color" size="20">{{ grp.icon }}</v-icon>
                  <span class="text-subtitle-2 font-weight-bold">{{ grp.label }}</span>
                  <v-chip size="x-small" :color="grp.color" variant="tonal">{{ grp.items.length }}</v-chip>
                </div>
                <v-list density="compact" class="py-0">
                  <v-list-item v-for="p in grp.items" :key="p.user_id" :title="p.name" :subtitle="p.email" />
                </v-list>
              </template>
            </div>
          </template>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snack" :color="snackColor" timeout="2500" location="top">{{ snackMsg }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { confirmAction } from '../services/confirm'
import { useAuthStore } from '../stores/auth'
import { downloadICS as icsDownload, googleCalendarUrl } from '../services/calendar'
import EventCardList from '../components/EventCardList.vue'

const auth = useAuthStore()

const events = ref([])
const loading = ref(true)
const busyId = ref(null)

const showForm = ref(false)
const editId = ref(null)
const saving = ref(false)

const showParticipants = ref(false)
const participants = ref([])

const snack = ref(false)
const snackMsg = ref('')
const snackColor = ref('success')

const defaultForm = () => ({
  title: '', description: '', location: '',
  start_at: '', end_at: '', is_public: true, notify: true,
})
const form = ref(defaultForm())

const now = new Date()
const upcoming = computed(() =>
  events.value.filter(e => new Date(e.end_at || e.start_at) >= now)
)
const past = computed(() =>
  events.value.filter(e => new Date(e.end_at || e.start_at) < now).reverse()
)

const participantGroups = computed(() => {
  const g = (key, label, icon, color) => ({ key, label, icon, color, items: participants.value.filter(p => p.response === key) })
  return [
    g('yes', 'Présents', 'mdi-check-circle', 'success'),
    g('maybe', 'Peut-être', 'mdi-help-circle', 'warning'),
    g('no', 'Absents', 'mdi-close-circle', 'error'),
  ]
})

function flash(msg, color = 'success') { snackMsg.value = msg; snackColor.value = color; snack.value = true }

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/events/')
    events.value = data
  } catch (e) {
    flash('Erreur de chargement des événements', 'error')
  } finally {
    loading.value = false
  }
}

async function doRsvp(ev, response) {
  busyId.value = ev.id
  try {
    const { data } = await api.post(`/events/${ev.id}/rsvp`, { response })
    const i = events.value.findIndex(e => e.id === ev.id)
    if (i !== -1) events.value[i] = { ...events.value[i], my_response: data.my_response, counts: data.counts }
    flash('Réponse enregistrée')
  } catch (e) {
    flash(e.response?.data?.detail || 'Erreur', 'error')
  } finally {
    busyId.value = null
  }
}

function toInput(dt) { return dt ? String(dt).slice(0, 16) : '' }

function openCreate() {
  editId.value = null
  form.value = defaultForm()
  showForm.value = true
}

function openEdit(ev) {
  editId.value = ev.id
  form.value = {
    title: ev.title, description: ev.description || '', location: ev.location || '',
    start_at: toInput(ev.start_at), end_at: toInput(ev.end_at),
    is_public: ev.is_public, notify: false,
  }
  showForm.value = true
}

async function save() {
  if (!form.value.title.trim()) { flash('Le titre est requis', 'error'); return }
  if (!form.value.start_at) { flash('La date de début est requise', 'error'); return }
  saving.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      description: form.value.description || null,
      location: form.value.location || null,
      start_at: form.value.start_at,
      end_at: form.value.end_at || null,
      is_public: form.value.is_public,
    }
    if (editId.value) {
      await api.put(`/events/${editId.value}`, payload)
      flash('Événement modifié')
    } else {
      await api.post('/events/', { ...payload, notify: form.value.notify })
      flash(form.value.notify && form.value.is_public ? 'Événement créé — adhérents notifiés' : 'Événement créé')
    }
    showForm.value = false
    await load()
  } catch (e) {
    flash(e.response?.data?.detail || 'Erreur lors de l\'enregistrement', 'error')
  } finally {
    saving.value = false
  }
}

async function removeEvent(ev) {
  if (!(await confirmAction(`Supprimer l'événement « ${ev.title} » ?`))) return
  try {
    await api.delete(`/events/${ev.id}`)
    events.value = events.value.filter(e => e.id !== ev.id)
    flash('Événement supprimé')
  } catch (e) {
    flash(e.response?.data?.detail || 'Erreur', 'error')
  }
}

async function openParticipants(ev) {
  participants.value = []
  showParticipants.value = true
  try {
    const { data } = await api.get(`/events/${ev.id}/participants`)
    participants.value = data
  } catch (e) {
    flash('Impossible de charger les participants', 'error')
  }
}

function downloadICS(ev) { icsDownload(ev) }
function openGoogle(ev) { window.open(googleCalendarUrl(ev), '_blank', 'noopener') }

onMounted(load)
</script>
