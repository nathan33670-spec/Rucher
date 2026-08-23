<template>
  <v-layout>
    <!-- Navigation latérale : tiroir temporaire (masqué par défaut) -->
    <v-navigation-drawer v-model="drawer" temporary width="272">
      <!-- En-tête : identité de l'application + utilisateur connecté -->
      <div class="rucher-drawer-head pa-4">
        <div class="d-flex align-center ga-3">
          <v-avatar color="primary" size="40" variant="flat">
            <v-icon size="22" color="white">mdi-bee</v-icon>
          </v-avatar>
          <div class="min-width-0">
            <div class="text-subtitle-2 font-weight-bold">Rucher Manager</div>
            <div class="text-caption r-muted text-truncate">
              {{ `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim() || auth.user?.email }}
            </div>
          </div>
        </div>
      </div>
      <v-divider />
      <!-- Navigation groupée par thème : le tiroir reste lisible même
           lorsque l'utilisateur dispose de tous les rôles. -->
      <v-list density="compact" nav class="py-2">
        <template v-for="group in navGroups" :key="group.label">
          <v-list-subheader v-if="group.items.length" class="px-4">{{ group.label }}</v-list-subheader>
          <v-list-item
            v-for="item in group.items"
            :key="item.title"
            :to="item.to"
            :prepend-icon="item.icon"
            :title="item.title"
            color="primary"
            rounded="lg"
            exact
            @click="drawer = false"
          />
        </template>
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

    <!-- Barre supérieure — claire et discrète : la couleur miel est
         réservée aux actions, ce qui allège nettement l'interface. -->
    <v-app-bar color="surface" density="compact" app flat class="rucher-app-bar">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-toolbar-title class="rucher-title">
        <v-icon size="19" color="primary" class="mr-2 d-none d-sm-inline">mdi-bee</v-icon>
        {{ pageTitle }}
      </v-toolbar-title>
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

      <!-- Sélecteur de rôle actif (à la volée) — si plusieurs rôles autorisés -->
      <v-menu location="bottom end" v-if="auth.authorizedRoles.length > 1">
        <template v-slot:activator="{ props }">
          <v-chip v-bind="props" class="ml-1" size="small" color="primary" variant="tonal" link title="Rôle utilisé">
            <v-icon size="16" start>{{ roleIcon(currentRole) }}</v-icon>
            <span class="d-none d-sm-inline">{{ roleLabel(currentRole) }}</span>
            <v-icon size="14" end class="d-none d-sm-inline">mdi-chevron-down</v-icon>
          </v-chip>
        </template>
        <v-list density="compact" min-width="240">
          <v-list-subheader>J'utilise le rôle</v-list-subheader>
          <v-list-item
            v-for="r in orderedRoles" :key="r"
            :prepend-icon="roleIcon(r)" :title="roleLabel(r)"
            :active="currentRole === r" @click="doSwitchRole(r)"
          >
            <template v-slot:append>
              <v-icon v-if="currentRole === r" size="18" color="primary">mdi-check</v-icon>
              <v-icon v-else-if="auth.defaultRole === r" size="14" color="accent">mdi-star</v-icon>
            </template>
          </v-list-item>
        </v-list>
      </v-menu>

      <!-- Nom cliquable → menu profil / déconnexion -->
      <v-menu location="bottom end">
        <template v-slot:activator="{ props }">
          <v-chip v-bind="props" class="ml-1" size="small" variant="text" link>
            <v-icon size="19" color="secondary">mdi-account-circle</v-icon>
            <span class="d-none d-sm-inline ml-1">{{ auth.user?.first_name }}</span>
          </v-chip>
        </template>
        <v-list density="compact" min-width="230">
          <v-list-item
            :title="`${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim() || auth.user?.email"
            :subtitle="auth.user?.email"
            prepend-icon="mdi-account-circle"
          />
          <template v-if="auth.authorizedRoles.length > 1">
            <v-divider />
            <v-list-subheader class="text-caption">Rôle par défaut (à la connexion)</v-list-subheader>
            <v-list-item
              v-for="r in orderedRoles" :key="'d' + r"
              density="compact" @click="doSetDefaultRole(r)"
            >
              <template v-slot:prepend>
                <v-icon size="18" :color="auth.defaultRole === r ? 'accent' : 'grey-lighten-1'">
                  {{ auth.defaultRole === r ? 'mdi-star' : 'mdi-star-outline' }}
                </v-icon>
              </template>
              <v-list-item-title class="text-body-2">{{ roleLabel(r) }}</v-list-item-title>
            </v-list-item>
          </template>
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
    <v-bottom-navigation v-if="isMobile" grow color="primary" class="rucher-bottom-nav" :elevation="0">
      <!-- « exact » : sans cela, /app (Accueil) resterait surligné sur
           toutes les sous-routes /app/... en plus de l'onglet courant. -->
      <v-btn v-for="item in mobileNav" :key="item.title" :to="item.to" exact>
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
            <v-list-item v-for="a in notif.alerts" :key="a.id" :class="{ 'rucher-unread': !a.read }" @click="notif.markRead(a.id)">
              <v-list-item-title>{{ a.message }}</v-list-item-title>
              <v-list-item-subtitle>{{ a.hiveName }} — {{ a.date }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
          <p v-else class="text-center r-muted">Aucune alerte</p>
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
    if (n > 0) syncMsg.value = `${n} visite(s) synchronisée(s)`
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
  loadAccess()
})
onUnmounted(() => window.removeEventListener('online', onOnline))

const unreadAlerts = computed(() => notif.alerts.filter((a) => !a.read).length)

// La trésorerie peut être ouverte en lecture à tous les membres (réglages admin).
const treasuryOpen = ref(false)
async function loadAccess() {
  try {
    const { data } = await api.get('/settings/access')
    treasuryOpen.value = !!data.treasury_read_all
  } catch { /* onglet simplement masqué */ }
}

const navGroups = computed(() => {
  const gestion = [
    { to: { name: 'inventory' }, icon: 'mdi-package-variant-closed', title: 'Inventaire' },
    { to: { name: 'honey' }, icon: 'mdi-bee-flower', title: 'Miellée' },
    { to: { name: 'sanitary' }, icon: 'mdi-medical-bag', title: 'Sanitaire' },
  ]
  if (auth.hasRole('treasurer') || auth.isAdmin || treasuryOpen.value) {
    gestion.push({ to: { name: 'treasury' }, icon: 'mdi-cash-register', title: 'Trésorerie' })
  }

  const reglages = [
    { to: { name: 'docs-home' }, icon: 'mdi-book-open-variant', title: 'Documentation' },
    { to: { name: 'notifications' }, icon: 'mdi-bell-cog', title: 'Notifications' },
    { to: { name: 'logs' }, icon: 'mdi-history', title: 'Journal' },
  ]
  if (auth.isAdmin) {
    reglages.splice(2, 0, { to: { name: 'users' }, icon: 'mdi-account-cog', title: 'Utilisateurs' })
    reglages.push({ to: { name: 'admin-settings' }, icon: 'mdi-cog-outline', title: 'Configuration' })
  }

  return [
    {
      label: 'Suivi du rucher',
      items: [
        { to: { name: 'dashboard' }, icon: 'mdi-view-dashboard-outline', title: 'Tableau de bord' },
        { to: { name: 'apiaries' }, icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
        { to: { name: 'visit-live-mine' }, icon: 'mdi-bee', title: 'Visite rapide' },
        { to: { name: 'visits' }, icon: 'mdi-clipboard-text-outline', title: 'Historique des visites' },
        { to: { name: 'weather' }, icon: 'mdi-weather-partly-cloudy', title: 'Météo' },
        { to: { name: 'events' }, icon: 'mdi-calendar-star', title: 'Événements' },
      ],
    },
    { label: 'Gestion', items: gestion },
    { label: 'Réglages', items: reglages },
  ]
})

const mobileNav = [
  { to: { name: 'dashboard' }, icon: 'mdi-home', title: 'Accueil' },
  { to: { name: 'visit-live-mine' }, icon: 'mdi-bee', title: 'Visite rapide' },
  { to: { name: 'apiaries' }, icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
  { to: { name: 'visits' }, icon: 'mdi-clipboard-text', title: 'Historique visites' },
  { to: { name: 'weather' }, icon: 'mdi-weather-partly-cloudy', title: 'Météo' },
]

const pageTitle = computed(() => {
  const titles = {
    dashboard: 'Tableau de bord',
    apiaries: 'Ruchers',
    visits: 'Historique des visites',
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
    'admin-settings': 'Configuration',
  }
  return titles[route.name] || 'Rucher Manager'
})

// ─── Rôles (commutation à la volée + par défaut) ─────────
const ROLE_LABELS = { admin: 'Administrateur', treasurer: 'Trésorier', yard_manager: 'Responsable rucher', user: 'Usager', readonly: 'Lecture seule' }
const ROLE_ICONS = { admin: 'mdi-shield-crown', treasurer: 'mdi-cash', yard_manager: 'mdi-hexagon-multiple', user: 'mdi-account', readonly: 'mdi-eye' }
const ROLE_ORDER = ['admin', 'yard_manager', 'treasurer', 'user', 'readonly']
function roleLabel(r) { return ROLE_LABELS[r] || r }
function roleIcon(r) { return ROLE_ICONS[r] || 'mdi-account' }
const orderedRoles = computed(() => [...auth.authorizedRoles].sort((a, b) => ROLE_ORDER.indexOf(a) - ROLE_ORDER.indexOf(b)))
const currentRole = computed(() => auth.activeRole || orderedRoles.value[0])

async function doSwitchRole(r) {
  if (r === currentRole.value) return
  try {
    await auth.switchRole(r)
    syncMsg.value = 'Vous utilisez maintenant : ' + roleLabel(r)
    // Si la page courante n'est plus autorisée, revenir à l'accueil.
    if (route.name && !isRouteAllowed(route.name)) router.push({ name: 'dashboard' })
  } catch {
    syncMsg.value = 'Changement de rôle impossible'
  }
}
async function doSetDefaultRole(r) {
  // Re-cliquer sur le rôle par défaut actuel l'annule (→ tous les rôles à la connexion).
  const target = auth.defaultRole === r ? null : r
  try {
    await auth.setDefaultRole(target)
    syncMsg.value = target
      ? 'Rôle par défaut : ' + roleLabel(target)
      : 'Rôle par défaut annulé (tous les rôles)'
  } catch { syncMsg.value = 'Impossible d\'enregistrer le rôle par défaut' }
}
function isRouteAllowed(name) {
  if (name === 'treasury') return auth.hasRole('treasurer') || auth.isAdmin || treasuryOpen.value
  if (name === 'users' || name === 'admin-settings') return auth.isAdmin
  return true
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
/* Barre supérieure : filet fin au lieu d'une ombre, translucide au défilement. */
.rucher-app-bar {
  border-bottom: 1px solid var(--r-hairline);
  background-color: rgba(255, 255, 255, 0.86) !important;
}

.rucher-title {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.012em;
}

/* Sur téléphone, la barre porte aussi les puces rôle/profil : on réduit
   légèrement le titre et ses marges pour qu'il ne soit plus tronqué. */
@media (max-width: 599px) {
  .rucher-title {
    font-size: 0.9375rem;
    margin-inline-start: 4px !important;
    padding-inline: 0 !important;
  }
}

/* En-tête du tiroir : léger dégradé miel, très discret. */
.rucher-drawer-head {
  background: linear-gradient(135deg, rgba(198, 138, 18, 0.1), rgba(198, 138, 18, 0.02));
}

.min-width-0 {
  min-width: 0;
}

/* Barre de navigation mobile : toujours visible, fixée en bas de l'écran */
.rucher-bottom-nav {
  position: fixed !important;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1006;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  height: calc(56px + env(safe-area-inset-bottom, 0px)) !important;
  border-top: 1px solid var(--r-hairline);
  background-color: rgba(255, 255, 255, 0.94) !important;
  backdrop-filter: saturate(140%) blur(10px);
}

/* Libellés de la barre mobile : compacts, sans majuscules, sur deux lignes
   si nécessaire — « Visite rapide » et « Historique visites » doivent rester
   lisibles en entier, l'abréviation recréerait l'ambiguïté. */
.rucher-bottom-nav :deep(.v-btn) {
  text-transform: none;
  letter-spacing: -0.01em;
  font-weight: 500;
  min-width: 0;
  padding-inline: 2px;
}

.rucher-bottom-nav :deep(.v-btn__content) {
  flex-direction: column;
  row-gap: 1px;
}

.rucher-bottom-nav :deep(.v-btn__content > .text-caption) {
  font-size: 0.625rem;
  line-height: 1.15;
  white-space: normal;
  text-align: center;
  max-width: 100%;
}

/* Alerte non lue : liseré miel à gauche plutôt qu'un aplat jaune. */
.rucher-unread {
  background-color: rgba(198, 138, 18, 0.07);
  box-shadow: inset 3px 0 0 #C68A12;
}
</style>
