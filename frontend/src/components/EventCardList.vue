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

          <template v-if="isAdmin">
            <v-btn size="small" variant="text" prepend-icon="mdi-account-group" @click="$emit('participants', ev)">Participants</v-btn>
            <v-btn icon size="small" variant="text" @click="$emit('edit', ev)"><v-icon>mdi-pencil</v-icon></v-btn>
            <v-btn icon size="small" variant="text" @click="$emit('remove', ev)"><v-icon color="error">mdi-delete</v-icon></v-btn>
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
  busyId: { type: [Number, null], default: null },
})
const emit = defineEmits(['rsvp', 'edit', 'remove', 'participants', 'calendar-ics', 'calendar-google'])

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
