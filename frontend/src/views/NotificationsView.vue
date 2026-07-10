<template>
  <div style="max-width: 640px; margin: 0 auto;">
    <h2 class="mb-1">Notifications</h2>
    <p class="text-body-2 text-medium-emphasis mb-4">
      Recevez une notification sur votre téléphone lors des événements que vous choisissez.
    </p>

    <v-alert v-if="msg" :type="msgType" density="compact" class="mb-4" closable @click:close="msg = ''">{{ msg }}</v-alert>

    <!-- Non supporté -->
    <v-alert v-if="!state.supported" type="warning" variant="tonal" class="mb-4">
      Votre navigateur ne prend pas en charge les notifications push.
    </v-alert>

    <!-- iOS : installation requise -->
    <v-alert v-else-if="iOS && !standalone" type="info" variant="tonal" class="mb-4">
      <b>Sur iPhone/iPad :</b> les notifications ne fonctionnent qu'une fois l'application
      <b>installée</b> (Safari → Partager → « Sur l'écran d'accueil »), puis ouverte depuis l'icône.
    </v-alert>

    <template v-if="state.supported">
      <!-- Interrupteur principal -->
      <v-card variant="tonal" :color="active ? 'primary' : undefined" class="mb-4">
        <v-card-item>
          <template v-slot:prepend>
            <v-icon size="32">{{ active ? 'mdi-bell-ring' : 'mdi-bell-off' }}</v-icon>
          </template>
          <v-card-title class="text-subtitle-1 font-weight-bold">
            {{ active ? 'Notifications activées' : 'Activer les notifications' }}
          </v-card-title>
          <v-card-subtitle class="text-wrap">Sur cet appareil</v-card-subtitle>
          <template v-slot:append>
            <v-switch :model-value="active" color="primary" :loading="busy" hide-details inset
              @update:model-value="toggleActive" />
          </template>
        </v-card-item>
      </v-card>

      <!-- Catégories -->
      <v-card variant="outlined" :disabled="!active" class="mb-4">
        <v-list>
          <v-list-subheader>Je veux être notifié pour…</v-list-subheader>
          <v-list-item v-for="c in categories" :key="c.key" :prepend-icon="c.icon" :title="c.label" :subtitle="c.desc">
            <template v-slot:append>
              <v-switch :model-value="prefs[c.key]" color="primary" hide-details inset
                @update:model-value="(v) => updatePref(c.key, v)" />
            </template>
          </v-list-item>
        </v-list>
      </v-card>

      <v-btn v-if="active" variant="tonal" color="primary" class="text-none" prepend-icon="mdi-bell-check"
        :loading="testing" @click="test">
        Envoyer une notification de test
      </v-btn>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { pushSupported, isStandalone, isIOS, getPushState, enablePush, disablePush, getPrefs, setPrefs, sendTest, resyncSubscription } from '../services/push'

const state = reactive({ supported: pushSupported(), subscribed: false, permission: 'default' })
const standalone = isStandalone()
const iOS = isIOS
const active = ref(false)
const busy = ref(false)
const testing = ref(false)
const msg = ref('')
const msgType = ref('success')
const prefs = reactive({ enabled: true, visits: true, inventory: true, alerts: true, sanitary: true, treasury: false, events: true })

const categories = [
  { key: 'events', icon: 'mdi-calendar-star', label: 'Événements', desc: 'Une sortie ou réunion est annoncée' },
  { key: 'visits', icon: 'mdi-clipboard-text', label: 'Nouvelle visite', desc: 'Quand une visite est saisie' },
  { key: 'inventory', icon: 'mdi-package-variant', label: 'Mouvement de matériel', desc: 'Entrée, sortie, déplacement' },
  { key: 'alerts', icon: 'mdi-alert', label: 'Alerte terrain', desc: 'Problème signalé sur une ruche' },
  { key: 'sanitary', icon: 'mdi-medical-bag', label: 'Sanitaire', desc: 'Traitement ou comptage varroa' },
  { key: 'treasury', icon: 'mdi-cash-register', label: 'Trésorerie', desc: 'Nouvelle écriture' },
]

function flash(text, type = 'success') { msg.value = text; msgType.value = type }

async function refresh() {
  const s = await getPushState()
  Object.assign(state, s)
  // Auto-réparation : si l'appareil est abonné localement, on ré-enregistre
  // l'abonnement côté serveur au cas où il y manquerait (abonnement créé
  // pendant une panne serveur). Idempotent (upsert par endpoint).
  if (s.subscribed) {
    try { await resyncSubscription() } catch { /* ignore */ }
  }
  try {
    const p = await getPrefs()
    Object.assign(prefs, p)
  } catch { /* ignore */ }
  active.value = state.subscribed && prefs.enabled
}

async function toggleActive(val) {
  busy.value = true
  try {
    if (val) {
      await enablePush()
      await setPrefs({ enabled: true })
      active.value = true
      flash('Notifications activées sur cet appareil.')
    } else {
      await disablePush()
      await setPrefs({ enabled: false })
      active.value = false
      flash('Notifications désactivées.')
    }
  } catch (e) {
    active.value = false
    flash(e.message || 'Impossible d\'activer les notifications.', 'error')
  } finally {
    busy.value = false
    await refresh()
  }
}

async function updatePref(key, val) {
  prefs[key] = val
  try { await setPrefs({ [key]: val }) } catch { flash('Enregistrement impossible.', 'error') }
}

async function test() {
  testing.value = true
  try {
    const { sent } = await sendTest()
    flash(sent > 0 ? 'Notification de test envoyée !' : 'Aucun appareil abonné — activez d\'abord les notifications.', sent > 0 ? 'success' : 'warning')
  } catch { flash('Échec de l\'envoi du test.', 'error') } finally { testing.value = false }
}

onMounted(refresh)
</script>
