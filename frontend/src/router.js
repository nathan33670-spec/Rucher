import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const routes = [
  { path: '/', name: 'landing', component: () => import('./views/LandingView.vue') },
  { path: '/login', name: 'login', component: () => import('./views/LoginView.vue') },
  {
    // Documentation — PUBLIQUE (accessible sans connexion)
    path: '/docs',
    component: () => import('./layouts/DocsLayout.vue'),
    children: [
      { path: '', name: 'docs-home', component: () => import('./views/docs/DocsHome.vue') },
      { path: 'memo', name: 'docs-memo', component: () => import('./views/docs/MemoView.vue') },
      { path: 'guide', name: 'docs-guide', component: () => import('./views/docs/GuideView.vue') },
      { path: 'cycle-abeille', name: 'docs-cycle', component: () => import('./views/docs/CycleAbeilleView.vue') },
      { path: 'varroa', name: 'docs-varroa', component: () => import('./views/docs/VarroaView.vue') },
      { path: 'reglementation', name: 'docs-reglementation', component: () => import('./views/docs/ReglementationView.vue') },
      { path: 'nouveau', name: 'docs-new', component: () => import('./views/docs/DocEditorView.vue'), meta: { requiresAuth: true } },
      { path: 'editer/:slug', name: 'docs-edit', component: () => import('./views/docs/DocEditorView.vue'), props: true, meta: { requiresAuth: true } },
      { path: 'p/:slug', name: 'docs-page', component: () => import('./views/docs/DynamicDocView.vue'), props: true },
    ],
  },
  {
    path: '/app',
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
      { path: 'weather', name: 'weather', component: () => import('./views/WeatherView.vue') },
      { path: 'notifications', name: 'notifications', component: () => import('./views/NotificationsView.vue') },
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
  // Déjà connecté mais on tente d'aller sur /login → vers le tableau de bord
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  // Sinon, navigation autorisée
  return true
})

export default router
