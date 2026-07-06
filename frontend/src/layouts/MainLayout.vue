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
          <v-chip v-bind="props" class="ml-2" size="small" variant="tonal" link>
            <v-icon start size="16">mdi-account-circle</v-icon>
            {{ auth.user?.first_name }}
          </v-chip>
        </template>
        <v-list density="compact" min-width="220">
          <v-list-item
            :title="`${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim()"
            :subtitle="auth.user?.email"
            prepend-icon="mdi-account-circle"
          />
          <v-divider />
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
import { canInstall } from '../services/pwa'
import InstallButton from '../components/InstallButton.vue'

const auth = useAuthStore()
const notif = useNotifStore()
const router = useRouter()
const route = useRoute()
const { mobile } = useDisplay()

const drawer = ref(false)
const showAlerts = ref(false)
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

onMounted(async () => {
  await refreshPendingCount()
  if (navigator.onLine) syncNow()
  window.addEventListener('online', onOnline)
})
onUnmounted(() => window.removeEventListener('online', onOnline))

const unreadAlerts = computed(() => notif.alerts.filter((a) => !a.read).length)

const navItems = computed(() => {
  const items = [
    { to: { name: 'dashboard' }, icon: 'mdi-view-dashboard', title: 'Tableau de bord' },
    { to: { name: 'apiaries' }, icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
    { to: { name: 'visits' }, icon: 'mdi-clipboard-text', title: 'Visites' },
    { to: { name: 'weather' }, icon: 'mdi-weather-partly-cloudy', title: 'Météo' },
    { to: { name: 'inventory' }, icon: 'mdi-package-variant-closed', title: 'Inventaire' },
    { to: { name: 'honey' }, icon: 'mdi-bee-flower', title: 'Miellée' },
    { to: { name: 'sanitary' }, icon: 'mdi-medical-bag', title: 'Sanitaire' },
    { to: { name: 'docs-home' }, icon: 'mdi-book-open-variant', title: 'Documentation' },
    { to: { name: 'logs' }, icon: 'mdi-history', title: 'Journal' },
  ]
  if (auth.hasRole('treasurer') || auth.isAdmin) items.push({ to: { name: 'treasury' }, icon: 'mdi-cash-register', title: 'Trésorerie' })
  if (auth.isAdmin) items.push({ to: { name: 'users' }, icon: 'mdi-account-cog', title: 'Utilisateurs' })
  return items
})

const mobileNav = [
  { to: { name: 'dashboard' }, icon: 'mdi-home', title: 'Accueil' },
  { to: { name: 'apiaries' }, icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
  { to: { name: 'visits' }, icon: 'mdi-clipboard-text', title: 'Visites' },
  { to: { name: 'weather' }, icon: 'mdi-weather-partly-cloudy', title: 'Météo' },
  { to: { name: 'logs' }, icon: 'mdi-history', title: 'Logs' },
]

const pageTitle = computed(() => {
  const titles = {
    dashboard: 'Tableau de bord',
    apiaries: 'Ruchers',
    visits: 'Visites',
    weather: 'Météo',
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
