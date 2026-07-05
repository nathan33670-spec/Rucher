<template>
  <v-layout>
    <!-- Navigation latérale -->
    <v-navigation-drawer v-model="drawer" :rail="rail" permanent app>
      <v-list-item
        prepend-icon="mdi-bee"
        title="Rucher Manager"
        @click="rail = !rail"
      />
      <v-divider />
      <v-list density="compact" nav>
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          exact
        />
      </v-list>
      <template v-slot:append>
        <v-list-item
          prepend-icon="mdi-logout"
          title="Déconnexion"
          @click="logout"
        />
      </template>
    </v-navigation-drawer>

    <!-- Barre supérieure -->
    <v-app-bar color="primary" density="compact" app>
      <v-app-bar-nav-icon @click="drawer = !drawer" class="d-md-none" />
      <v-toolbar-title>{{ pageTitle }}</v-toolbar-title>
      <v-spacer />

      <!-- Alertes -->
      <v-badge :content="unreadAlerts" :model-value="unreadAlerts > 0" color="error" overlap>
        <v-btn icon @click="showAlerts = true">
          <v-icon>mdi-bell</v-icon>
        </v-btn>
      </v-badge>

      <v-chip class="ml-2" size="small" variant="tonal">
        {{ auth.user?.first_name }}
      </v-chip>
    </v-app-bar>

    <!-- Contenu principal -->
    <v-main>
      <v-container fluid class="pa-4">
        <router-view />
      </v-container>
    </v-main>

    <!-- Bottom nav mobile -->
    <v-bottom-navigation v-if="isMobile" grow app color="primary">
      <v-btn v-for="item in mobileNav" :key="item.to" :to="item.to">
        <v-icon>{{ item.icon }}</v-icon>
        <span class="text-caption">{{ item.title }}</span>
      </v-btn>
    </v-bottom-navigation>

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
import { ref, computed } from 'vue'
import { useDisplay } from 'vuetify'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotifStore } from '../stores/notif'

const auth = useAuthStore()
const notif = useNotifStore()
const router = useRouter()
const route = useRoute()
const { mobile } = useDisplay()

const drawer = ref(true)
const rail = ref(false)
const showAlerts = ref(false)
const isMobile = computed(() => mobile.value)

const unreadAlerts = computed(() => notif.alerts.filter((a) => !a.read).length)

const navItems = computed(() => {
  const items = [
    { to: '/', icon: 'mdi-view-dashboard', title: 'Tableau de bord' },
    { to: '/apiaries', icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
    { to: '/visits', icon: 'mdi-clipboard-text', title: 'Visites' },
    { to: '/inventory', icon: 'mdi-package-variant-closed', title: 'Inventaire' },
    { to: '/honey', icon: 'mdi-bee-flower', title: 'Miellée' },
    { to: '/sanitary', icon: 'mdi-medical-bag', title: 'Sanitaire' },
    { to: '/logs', icon: 'mdi-history', title: 'Journal' },
  ]
  if (auth.hasRole('treasurer') || auth.isAdmin) items.push({ to: '/treasury', icon: 'mdi-cash-register', title: 'Trésorerie' })
  if (auth.isAdmin) items.push({ to: '/users', icon: 'mdi-account-cog', title: 'Utilisateurs' })
  return items
})

const mobileNav = [
  { to: '/', icon: 'mdi-home', title: 'Accueil' },
  { to: '/apiaries', icon: 'mdi-hexagon-multiple', title: 'Ruchers' },
  { to: '/visits', icon: 'mdi-clipboard-text', title: 'Visites' },
  { to: '/inventory', icon: 'mdi-package-variant-closed', title: 'Stock' },
  { to: '/logs', icon: 'mdi-history', title: 'Logs' },
]

const pageTitle = computed(() => {
  const titles = {
    dashboard: 'Tableau de bord',
    apiaries: 'Ruchers',
    visits: 'Visites',
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
