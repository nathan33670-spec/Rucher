import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('./views/LoginView.vue') },
  {
    path: '/',
    component: () => import('./layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'dashboard', component: () => import('./views/DashboardView.vue') },
      { path: 'apiaries', name: 'apiaries', component: () => import('./views/ApiaryView.vue') },
      { path: 'apiaries/:id', name: 'apiary-detail', component: () => import('./views/ApiaryDetailView.vue'), props: true },
      { path: 'visits', name: 'visits', component: () => import('./views/VisitsView.vue') },
      { path: 'visits/live/:apiaryId', name: 'visit-live', component: () => import('./views/VisitLiveView.vue'), props: true },
      { path: 'inventory', name: 'inventory', component: () => import('./views/InventoryView.vue') },
      { path: 'treasury', name: 'treasury', component: () => import('./views/TreasuryView.vue') },
      { path: 'honey', name: 'honey', component: () => import('./views/HoneyView.vue') },
      { path: 'sanitary', name: 'sanitary', component: () => import('./views/SanitaryView.vue') },
      { path: 'users', name: 'users', component: () => import('./views/UsersView.vue') },
      { path: 'logs', name: 'logs', component: () => import('./views/LogsView.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  // Route protégée sans session → vers la mire de connexion
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }
  // Déjà connecté mais on tente d'aller sur /login → vers l'accueil
  if (to.name === 'login' && auth.isAuthenticated) {
    return { path: '/' }
  }
  // Sinon, navigation autorisée
  return true
})

export default router
