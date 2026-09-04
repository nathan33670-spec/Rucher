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

      <v-btn v-if="active" variant="tonal" color="primary" prepend-icon="mdi-bell-check"
        :loading="testing" @click="test">
        Envoyer une notification de test
      </v-btn>
    </template>

    <!-- Diagnostic — administrateur : distingue un serveur muet d'un parc
         d'appareils simplement non abonnés. -->
    <v-card v-if="auth.isAdmin" variant="outlined" class="mt-6">
      <v-card-item>
        <v-card-title class="text-subtitle-1 font-weight-bold">
          <v-icon size="20" class="mr-1" color="secondary">mdi-stethoscope</v-icon>
          Diagnostic (administrateur)
        </v-card-title>
        <v-card-subtitle class="text-wrap">
          État réel du service de notifications pour toute l'association.
        </v-card-subtitle>
      </v-card-item>
      <v-card-text>
        <v-btn size="small" variant="tonal" :loading="diagLoading" prepend-icon="mdi-refresh"
          @click="loadDiagnostics">
          {{ diag ? 'Actualiser' : 'Analyser' }}
        </v-btn>

        <template v-if="diag">
          <div class="d-flex flex-wrap ga-2 my-3">
            <v-chip size="small" :color="diag.vapid_configured ? 'success' : 'error'" variant="tonal">
              <v-icon start size="14">{{ diag.vapid_configured ? 'mdi-key' : 'mdi-key-alert' }}</v-icon>
              Clés VAPID {{ diag.vapid_configured ? 'en place' : 'absentes' }}
            </v-chip>
            <v-chip size="small" :color="diag.total_devices ? 'primary' : 'warning'" variant="tonal">
              <v-icon start size="14">mdi-cellphone</v-icon>
              {{ diag.total_devices }} appareil(s) · {{ diag.users_with_device }} personne(s)
            </v-chip>
          </div>

          <v-alert v-if="!diag.total_devices" type="warning" variant="tonal" density="compact" class="mb-3">
            Aucun appareil abonné : personne ne peut recevoir de notification.
            Chaque adhérent doit activer l'interrupteur ci-dessus <b>depuis son
            téléphone</b> (et, sur iPhone, depuis l'application installée).
          </v-alert>

          <v-alert v-if="diag.last_send" :type="diag.last_send.sent ? 'success' : 'warning'"
            variant="tonal" density="compact" class="mb-3">
            Dernier envoi ({{ diag.last_send.at }}) : « {{ diag.last_send.title }} » —
            {{ diag.last_send.sent }}/{{ diag.last_send.targets }} appareil(s) servis<template
              v-if="diag.last_send.failed">, {{ diag.last_send.failed }} en échec</template><template
              v-if="diag.last_send.removed">, {{ diag.last_send.removed }} abonnement(s) périmé(s) supprimé(s)</template>.
            <div v-if="diag.last_send.error" class="text-caption mt-1">
              Cause : {{ diag.last_send.error }}
            </div>
          </v-alert>
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">
            Aucun envoi depuis le dernier redémarrage du serveur.
          </v-alert>

          <v-table density="compact">
            <thead>
              <tr><th>Adhérent</th><th class="text-center">Appareils</th><th>Reçoit</th></tr>
            </thead>
            <tbody>
              <tr v-for="u in diag.users" :key="u.id">
                <td>{{ u.name }}</td>
                <td class="text-center">
                  <v-chip size="x-small" :color="u.devices ? 'success' : 'default'" variant="tonal">
                    {{ u.devices }}
                  </v-chip>
                </td>
                <td class="text-caption">
                  <span v-if="!u.devices" class="text-medium-emphasis">non abonné</span>
                  <span v-else-if="u.enabled === false" class="text-medium-emphasis">tout coupé</span>
                  <span v-else-if="!u.categories.length">toutes catégories (par défaut)</span>
                  <span v-else>{{ u.categories.join(', ') }}</span>
                </td>
              </tr>
            </tbody>
          </v-table>
        </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../services/api'
import { apiError } from '../services/toast'
import { useAuthStore } from '../stores/auth'
import { pushSupported, isStandalone, isIOS, getPushState, enablePush, disablePush, getPrefs, setPrefs, sendTest, resyncSubscription } from '../services/push'

const state = reactive({ supported: pushSupported(), subscribed: false, permission: 'default' })
const standalone = isStandalone()
const iOS = isIOS
const active = ref(false)
const busy = ref(false)
const testing = ref(false)
const auth = useAuthStore()
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
    // e.message vient de push.js (permission refusée, non supporté) ;
    // sinon c'est une erreur d'API à traduire.
    flash(e?.response ? apiError(e, "Impossible d'activer les notifications.")
                      : (e.message || "Impossible d'activer les notifications."), 'error')
  } finally {
    busy.value = false
    await refresh()
  }
}

async function updatePref(key, val) {
  prefs[key] = val
  try { await setPrefs({ [key]: val }) }
  catch (e) { flash(apiError(e, 'Enregistrement impossible.'), 'error') }
}

async function test() {
  testing.value = true
  try {
    // Le serveur explique précisément ce qui s'est passé (aucun appareil
    // abonné, appareil refusé, envoi réussi) : on relaie son message.
    const data = await sendTest()
    flash(data.detail || 'Notification de test envoyée !', data.sent > 0 ? 'success' : 'warning')
  } catch (e) {
    flash(apiError(e, "Échec de l'envoi du test."), 'error')
  } finally {
    testing.value = false
  }
}

// ─── Diagnostic administrateur ───
const diag = ref(null)
const diagLoading = ref(false)
async function loadDiagnostics() {
  diagLoading.value = true
  try {
    const { data } = await api.get('/notifications/diagnostics')
    diag.value = data
  } catch (e) {
    flash(apiError(e, 'Diagnostic indisponible'), 'error')
  } finally {
    diagLoading.value = false
  }
}

onMounted(refresh)
</script>
