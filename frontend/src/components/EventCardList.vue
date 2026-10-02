<template>
  <v-row>
    <v-col v-for="ev in events" :key="ev.id" cols="12" md="6">
      <v-card :variant="past ? 'tonal' : 'elevated'" class="h-100 d-flex flex-column" :class="{ 'event-past': past }">
        <v-card-item>
          <template v-slot:prepend>
            <v-avatar :color="past ? 'grey' : 'primary'" variant="tonal" rounded>
              <div class="text-center" style="line-height:1;">
                <div class="text-caption font-weight-bold">{{ dayNum(ev.start_at) }}</div>
                <div style="font-size:10px;text-transform:uppercase;">{{ monthShort(ev.start_at) }}</div>
              </div>
            </v-avatar>
          </template>
          <v-card-title class="text-subtitle-1 text-wrap">{{ ev.title }}</v-card-title>
          <v-card-subtitle class="text-wrap">
            <v-icon size="14">mdi-clock-outline</v-icon> {{ whenLabel(ev) }}
          </v-card-subtitle>
          <template v-slot:append>
            <v-chip v-if="isAdmin && !ev.is_public" size="x-small" color="grey" variant="tonal" prepend-icon="mdi-lock">
              Privé
            </v-chip>
          </template>
        </v-card-item>

        <v-card-text class="py-1">
          <div v-if="ev.location" class="mb-1">
            <v-icon size="16" color="primary">mdi-map-marker</v-icon> {{ ev.location }}
          </div>
          <p v-if="ev.description" class="text-body-2 text-medium-emphasis mb-2" style="white-space:pre-line;">{{ ev.description }}</p>

          <!-- Réponses (compteurs) -->
          <div class="d-flex ga-2 flex-wrap mb-1">
            <v-chip size="small" color="success" variant="tonal" prepend-icon="mdi-check">{{ ev.counts.yes }} présent{{ ev.counts.yes > 1 ? 's' : '' }}</v-chip>
            <v-chip size="small" color="warning" variant="tonal" prepend-icon="mdi-help">{{ ev.counts.maybe }} peut-être</v-chip>
            <v-chip size="small" color="error" variant="tonal" prepend-icon="mdi-close">{{ ev.counts.no }} absent{{ ev.counts.no > 1 ? 's' : '' }}</v-chip>
          </div>
        </v-card-text>

        <v-spacer />

        <!-- RSVP : ma réponse -->
        <div v-if="!past" class="px-4 pb-1">
          <div class="text-caption text-medium-emphasis mb-1">
            {{ ev.my_response ? 'Votre réponse (modifiable) :' : 'Serez-vous présent ?' }}
          </div>
          <v-btn-toggle :model-value="ev.my_response" divided class="d-flex w-100" density="comfortable">
            <v-btn value="yes" color="success" class="flex-grow-1" :loading="busyId === ev.id && pending === 'yes'" @click="emitRsvp(ev, 'yes')">
              <v-icon start size="18">mdi-check</v-icon> Je viens
            </v-btn>
            <v-btn value="maybe" color="warning" class="flex-grow-1" :loading="busyId === ev.id && pending === 'maybe'" @click="emitRsvp(ev, 'maybe')">
              Peut-être
            </v-btn>
            <v-btn value="no" color="error" class="flex-grow-1" :loading="busyId === ev.id && pending === 'no'" @click="emitRsvp(ev, 'no')">
              <v-icon start size="18">mdi-close</v-icon> Absent
            </v-btn>
          </v-btn-toggle>
        </div>

        <v-card-actions>
          <!-- Ajouter au calendrier -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" size="small" variant="text" prepend-icon="mdi-calendar-plus">Calendrier</v-btn>
            </template>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-apple" title="Apple / Android (.ics)" @click="$emit('calendar-ics', ev)" />
              <v-list-item prepend-icon="mdi-google" title="Google Agenda" @click="$emit('calendar-google', ev)" />
            </v-list>
          </v-menu>

          <v-spacer />

          <!-- Partager : l'événement se diffuse là où les adhérents se
               parlent déjà, plutôt que de rester dans l'application. -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" size="small" variant="text" prepend-icon="mdi-share-variant">
                Partager
              </v-btn>
            </template>
            <v-list density="compact">
              <!-- Le partage natif ouvre le sélecteur du téléphone (WhatsApp,
                   SMS, Signal…). Absent sur ordinateur, d'où les entrées
                   explicites en dessous. -->
              <v-list-item
                v-if="partageNatif" prepend-icon="mdi-cellphone-message"
                title="Partager…" @click="partager(ev)"
              />
              <v-list-item prepend-icon="mdi-whatsapp" title="WhatsApp"
                           @click="versWhatsApp(ev)" />
              <v-list-item prepend-icon="mdi-email-outline" title="E-mail"
                           @click="versEmail(ev)" />
              <v-list-item prepend-icon="mdi-content-copy" title="Copier le texte"
                           @click="copier(ev)" />
            </v-list>
          </v-menu>

          <!-- L'organisateur relance son propre événement sans dépendre d'un
               administrateur : c'est lui qui sait quand c'est utile. -->
          <v-btn
            v-if="!past && canNotify(ev)"
            size="small" variant="text" prepend-icon="mdi-cellphone-message"
            :title="lastNotified(ev)"
            @click="$emit('notify', ev)"
          >
            Notifier
          </v-btn>

          <template v-if="peutOrganiser">
            <v-btn size="small" variant="text" prepend-icon="mdi-account-group" @click="$emit('participants', ev)">Participants</v-btn>
            <v-btn icon size="small" variant="text" @click="$emit('edit', ev)"><v-icon>mdi-pencil</v-icon></v-btn>
            <!-- Annuler l'événement d'un autre ne va pas de soi : réservé aux
                 administrateurs et à l'organisateur. -->
            <v-btn
              v-if="isAdmin || (userId != null && ev.created_by === userId)"
              icon size="small" variant="text" @click="$emit('remove', ev)"
            ><v-icon color="error">mdi-delete</v-icon></v-btn>
          </template>
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  events: { type: Array, default: () => [] },
  past: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
  // Administrateurs, trésoriers et responsables de rucher : ceux qui créent
  // et modifient les événements. Distinct de « isAdmin », qui garde ce qui
  // relève vraiment de l'administration (voir un événement privé d'autrui).
  peutOrganiser: { type: Boolean, default: false },
  // Identifiant de l'utilisateur courant : l'organisateur d'un événement peut
  // le relancer, même s'il n'est pas administrateur.
  userId: { type: [Number, null], default: null },
  busyId: { type: [Number, null], default: null },
})
const emit = defineEmits(['rsvp', 'edit', 'remove', 'participants', 'calendar-ics',
                          'calendar-google', 'notify', 'shared'])

// Le partage natif n'existe que sur mobile et en contexte sécurisé.
const partageNatif = typeof navigator !== 'undefined' && !!navigator.share

/** Le texte partagé : tout ce qu'il faut pour décider de venir. */
function texteEvenement(ev) {
  const quand = new Date(ev.start_at).toLocaleDateString('fr-FR',
    { weekday: 'long', day: 'numeric', month: 'long' })
  const heure = new Date(ev.start_at).toLocaleTimeString('fr-FR',
    { hour: '2-digit', minute: '2-digit' })
  const lignes = [`🐝 ${ev.title}`, `📅 ${quand} à ${heure}`]
  if (ev.location) lignes.push(`📍 ${ev.location}`)
  if (ev.description) lignes.push('', ev.description)
  lignes.push('', lienEvenement())
  return lignes.join('\n')
}

/** Adresse publique de l'application : celle par laquelle on la consulte. */
function lienEvenement() {
  return typeof window !== 'undefined' ? window.location.origin + '/app/events' : ''
}

async function partager(ev) {
  try {
    await navigator.share({ title: ev.title, text: texteEvenement(ev) })
  } catch { /* partage abandonné par l'utilisateur */ }
}

function versWhatsApp(ev) {
  window.open('https://wa.me/?text=' + encodeURIComponent(texteEvenement(ev)), '_blank')
}

function versEmail(ev) {
  window.location.href = 'mailto:?subject=' + encodeURIComponent(ev.title)
    + '&body=' + encodeURIComponent(texteEvenement(ev))
}

async function copier(ev) {
  try {
    await navigator.clipboard.writeText(texteEvenement(ev))
    emit('shared', 'Texte copié — collez-le où vous voulez')
  } catch {
    emit('shared', "La copie a échoué : sélectionnez le texte à la main")
  }
}

function canNotify(ev) {
  return props.isAdmin || (props.userId != null && ev.created_by === props.userId)
}

function lastNotified(ev) {
  if (!ev.last_notified_at) return "Aucune notification envoyée pour l'instant"
  const d = new Date(ev.last_notified_at)
  return 'Dernière notification : ' + d.toLocaleDateString('fr-FR')
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

const pending = ref(null)
function emitRsvp(ev, response) {
  pending.value = response
  emit('rsvp', ev, response)
}

function dayNum(dt) { return new Date(dt).getDate() }
function monthShort(dt) {
  return new Date(dt).toLocaleDateString('fr-FR', { month: 'short' }).replace('.', '')
}
function whenLabel(ev) {
  const opts = { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }
  const start = new Date(ev.start_at).toLocaleDateString('fr-FR', opts)
  if (ev.end_at) {
    const sameDay = new Date(ev.start_at).toDateString() === new Date(ev.end_at).toDateString()
    const endFmt = new Date(ev.end_at).toLocaleString('fr-FR', sameDay
      ? { hour: '2-digit', minute: '2-digit' }
      : opts)
    return `${start} → ${endFmt}`
  }
  return start
}
</script>

<style scoped>
.event-past { opacity: 0.75; }
</style>
