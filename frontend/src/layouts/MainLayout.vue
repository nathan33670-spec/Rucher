<template>
  <v-layout>
    <!-- Navigation latérale : tiroir temporaire (masqué par défaut) -->
    <v-navigation-drawer v-model="drawer" temporary>
      <v-list-item
        prepend-icon="mdi-bee"
        title="Rucher Manager"
        :to="{ name: 'dashboard' }"
        @click="drawer = false"
      />
      <v-divider />
      <v-list density="compact" nav>
        <v-list-item
          v-for="item in navItems"
          :key="item.title"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          exact
          @click="drawer = false"
        />
      </v-list>
      <template v-slot:append>
        <div v-if="canInstall" class="pa-2">
          <InstallButton block label="Installer l'app" />
        </div>
        <v-list-item
          prepend-icon="mdi-logout"
          title="Déconnexion"
          @click="logout"
        />
      </template>
    </v-navigation-drawer>

    <!-- Barre supérieure -->
    <v-app-bar color="primary" density="compact" app>
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-toolbar-title>{{ pageTitle }}</v-toolbar-title>
      <v-spacer />

      <!-- Visites hors-ligne en attente de synchronisation -->
      <v-btn
        v-if="pendingCount > 0"
        icon
        :loading="syncing"
        title="Synchroniser les visites enregistrées hors-ligne"
        @click="syncNow"
      >
        <v-badge :content="pendingCount" color="warning">
          <v-icon>mdi-cloud-sync</v-icon>
        </v-badge>
      </v-btn>

      <!-- Alertes -->
      <v-badge :content="unreadAlerts" :model-value="unreadAlerts > 0" color="error" overlap>
        <v-btn icon @click="showAlerts = true">
          <v-icon>mdi-bell</v-icon>
        </v-btn>
      </v-badge>

      <!-- Nom cliquable → menu profil / déconnexion -->
      <v-menu location="bottom end">
        <template v-slot:activator="{ props }">
          <v-chip v-bind="props" class="ml-1" size="small" variant="tonal" link>
            <v-icon size="18">mdi-account-circle</v-icon>
            <span class="d-none d-sm-inline ml-1">{{ auth.user?.first_name }}</span>
          </v-chip>
        </template>
        <v-list density="compact" min-width="220">
          <v-list-item
            :title="`${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim() || auth.user?.email"
            :subtitle="auth.user?.email"
            prepend-icon="mdi-account-circle"
          />
          <v-divider />
          <v-list-item
            prepend-icon="mdi-lock-reset"
            title="Changer mon mot de passe"
            @click="showChangePw = true"
          />
          <v-list-item
            prepend-icon="mdi-logout"
            title="Se déconnecter"
            base-color="error"
            @click="logout"
          />
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Contenu principal -->
    <v-main>
      <v-container fluid class="pa-4" :style="isMobile ? 'padding-bottom: 88px' : ''">
        <router-view />
      </v-container>
    </v-main>

    <!-- Bottom nav mobile — toujours visible (fixée en bas) -->
    <v-bottom-navigation v-if="isMobile" grow color="primary" class="rucher-bottom-nav" :elevation="8">
      <v-btn v-for="item in mobileNav" :key="item.title" :to="item.to">
        <v-icon>{{ item.icon }}</v-icon>
        <span class="text-caption">{{ item.title }}</span>
      </v-btn>
    </v-bottom-navigation>

    <!-- Notification de synchronisation hors-ligne -->
    <v-snackbar v-model="showSyncMsg" color="success" timeout="2500" location="top">
      {{ syncMsg }}
    </v-snackbar>

    <!-- Changer son propre mot de passe -->
    <ChangePasswordDialog v-model="showChangePw" @done="syncMsg = 'Mot de passe modifié'" />

    <!-- Demande d'activation des notifications au 1er lancement (après installation) -->
    <v-dialog v-model="showNotifPrompt" max-width="420" persistent>
      <v-card>
        <v-card-item>
          <template v-slot:prepend><v-icon size="36" color="primary">mdi-bell-ring</v-icon></template>
          <v-card-title>Activer les notifications ?</v-card-title>
        </v-card-item>
        <v-card-text>
          Soyez prévenu sur ce téléphone des événements de l'association (sorties, réunions),
          des nouvelles visites et des alertes. Vous pourrez tout régler ensuite dans l'onglet
          <b>Notifications</b>.
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="dismissNotifPrompt">Plus tard</v-btn>
          <v-spacer />
          <v-btn color="primary" variant="flat" :loading="notifPromptBusy" @click="acceptNotifPrompt">
            Activer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Panneau alertes -->
    <v-dialog v-model="showAlerts" max-width="500">
      <v-card>
        <v-card-title>🔔 Alertes</v-card-title>
        <v-card-text>
          <v-list v-if="notif.alerts.length">
            <v-list-item v-for="a in notif.alerts" :key="a.id" :class="{ 'bg-amber-lighten-5': !a.read }" @click="notif.markRead(a.id)">
              <v-list-item-title>{{ a.message }}</v-list-item-title>
              <v-list-item-subtitle>{{ a.hiveName }} — {{ a.date }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <p v-else class="text-center text-grey">Aucune alerte</p>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDisplay } from 'vuetify'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotifStore } from '../stores/notif'
import api from '../services/api'
import { pendingCount, refreshPendingCount, syncPendingVisits } from '../services/offline'
import { resyncSubscription, pushSupported, isStandalone, getPushState, enablePush } from '../services/push'
import { canInstall } from '../services/pwa'
import InstallButton from '../components/InstallButton.vue'
import ChangePasswordDialog from '../components/ChangePasswordDialog.vue'

const auth = useAuthStore()
const notif = useNotifStore()
const router = useRouter()
const route = useRoute()
const { mobile } = useDisplay()

const drawer = ref(false)
const showAlerts = ref(false)
const showChangePw = ref(false)
const showNotifPrompt = ref(false)
const notifPromptBusy = ref(false)
const syncing = ref(false)
const isMobile = computed(() => mobile.value)

// ─── Synchronisation globale des visites hors-ligne ───────────────
const syncMsg = ref('')
const showSyncMsg = computed({
  get: () => !!syncMsg.value,
  set: (v) => { if (!v) syncMsg.value = '' },
})
async function syncNow() {
  syncing.value = true
  try {
    const n = await syncPendingVisits(api)
    if (n > 0) syncMsg.value = `✅ ${n} visite(s) synchronisée(s)`
  } finally {
    syncing.value = false
  }
}
function onOnline() { syncNow() }

const NOTIF_PROMPT_KEY = 'notif_prompt_seen'

async function maybeAskNotifications() {
  // Proposé une seule fois, au 1er lancement de l'app installée (écran d'accueil).
  if (localStorage.getItem(NOTIF_PROMPT_KEY)) return
  if (!pushSupported() || !isStandalone()) return
  try {
    const st = await getPushState()
    // On ne propose que si l'utilisateur n'a pas encore choisi (ni abonné, ni refusé).
    if (st.subscribed || st.permission !== 'default') return
    showNotifPrompt.value = true
  } catch { /* ignore */ }
}

async function acceptNotifPrompt() {
  notifPromptBusy.value = true
  try {
    await enablePush()
    syncMsg.value = 'Notifications activées'
  } catch (e) {
    syncMsg.value = 'Notifications non activées (autorisation refusée)'
  } finally {
    localStorage.setItem(NOTIF_PROMPT_KEY, '1')
    notifPromptBusy.value = false
    showNotifPrompt.value = false
  }
}

function dismissNotifPrompt() {
  localStorage.setItem(NOTIF_PROMPT_KEY, '1')
  showNotifPrompt.value = false
}

onMounted(async () => {
  await refreshPendingCount()
  if (navigator.onLine) syncNow()
  window.addEventListener('online', onOnline)
  // Auto-réparation silencieuse : ré-enregistre l'abonnement push de cet
  // appareil s'il existe (corrige les abonnements perdus côté serveur).
  resyncSubscription().catch(() => {})
  // Proposition d'activation des notifications au 1er lancement (installé).
  maybeAskNotifications()
})
onUnmounted(() => window.removeEventListener('online', onOnline))

const unreadAlerts = computed(() => notif.alerts.filter((a) => !a.read).length)

const navItems = computed(() => {
  const items = [
    { to: { name: 'dashboard' }, icon: 'mdi-view-dashboard', title: 'Tableau de bord' },
    { to: { name: 'apiaries' }, icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
    { to: { name: 'visits' }, icon: 'mdi-clipboard-text', title: 'Visites' },
    { to: { name: 'weather' }, icon: 'mdi-weather-partly-cloudy', title: 'Météo' },
    { to: { name: 'events' }, icon: 'mdi-calendar-star', title: 'Événements' },
    { to: { name: 'inventory' }, icon: 'mdi-package-variant-closed', title: 'Inventaire' },
    { to: { name: 'honey' }, icon: 'mdi-bee-flower', title: 'Miellée' },
    { to: { name: 'sanitary' }, icon: 'mdi-medical-bag', title: 'Sanitaire' },
    { to: { name: 'docs-home' }, icon: 'mdi-book-open-variant', title: 'Documentation' },
    { to: { name: 'notifications' }, icon: 'mdi-bell-cog', title: 'Notifications' },
    { to: { name: 'logs' }, icon: 'mdi-history', title: 'Journal' },
  ]
  if (auth.hasRole('treasurer') || auth.isAdmin) items.push({ to: { name: 'treasury' }, icon: 'mdi-cash-register', title: 'Trésorerie' })
  if (auth.isAdmin) items.push({ to: { name: 'users' }, icon: 'mdi-account-cog', title: 'Utilisateurs' })
  return items
})

const mobileNav = [
  { to: { name: 'dashboard' }, icon: 'mdi-home', title: 'Accueil' },
  { to: { name: 'visit-live-mine' }, icon: 'mdi-bee', title: 'Visite' },
  { to: { name: 'apiaries' }, icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
  { to: { name: 'visits' }, icon: 'mdi-clipboard-text', title: 'Historique' },
  { to: { name: 'weather' }, icon: 'mdi-weather-partly-cloudy', title: 'Météo' },
]

const pageTitle = computed(() => {
  const titles = {
    dashboard: 'Tableau de bord',
    apiaries: 'Ruchers',
    visits: 'Visites',
    'visit-live-mine': 'Visite rapide',
    weather: 'Météo',
    events: 'Événements',
    notifications: 'Notifications',
    inventory: 'Inventaire',
    treasury: 'Trésorerie',
    honey: 'Miellée',
    sanitary: 'Sanitaire',
    users: 'Utilisateurs',
    logs: 'Journal',
  }
  return titles[route.name] || 'Rucher Manager'
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* Barre de navigation mobile : toujours visible, fixée en bas de l'écran */
.rucher-bottom-nav {
  position: fixed !important;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1006;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  height: calc(56px + env(safe-area-inset-bottom, 0px)) !important;
}
</style>
