import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({ baseURL: '/api' })

// Démonstration publique : aucun serveur derrière, l'API est simulée dans le
// navigateur. Le code n'est embarqué que si VITE_DEMO vaut 1 — en production,
// l'import dynamique est éliminé au moment du build.
export const MODE_DEMO = import.meta.env.VITE_DEMO === '1'

// L'application attend cette promesse avant de se monter : sans cela, les
// premières requêtes partiraient vers une API inexistante pendant que
// l'adaptateur est encore en train de se charger.
export const demoPrete = MODE_DEMO
  ? import('../demo/adaptateur').then(({ adaptateurDemo, utilisateurDemo }) => {
      api.defaults.adapter = adaptateurDemo
      return utilisateurDemo()
    })
  : Promise.resolve(null)

let _authStore = null
let _router = null

/**
 * Permet à l'application d'injecter le router pour effectuer des redirections
 * SPA (sans rechargement complet de la page). Appelé depuis main.js.
 */
export function attachRouter(router) {
  _router = router
}

function getAuthStore() {
  if (!_authStore) {
    try {
      _authStore = useAuthStore()
    } catch {
      _authStore = null
    }
  }
  return _authStore
}

// ─── Requête : ajoute le jeton JWT ───────────────────────────────
api.interceptors.request.use((config) => {
  const store = getAuthStore()
  const token = store?.token || localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Réponse : gère l'expiration / l'absence de session ──────────
api.interceptors.response.use(
  (r) => r,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''
    const tokenSent = !!error.config?.headers?.Authorization
    const isLoginCall = url.includes('/users/login')

    // 401 = jeton présent mais invalide/expiré → session terminée.
    // 403 SANS jeton = utilisateur non authentifié.
    // (Un 403 AVEC jeton correspond à un manque de droits : on n'y touche pas.)
    const sessionExpired = status === 401 && !isLoginCall
    const notAuthenticated = status === 403 && !tokenSent && !isLoginCall

    if (sessionExpired || notAuthenticated) {
      const store = getAuthStore()
      if (store) store.logout()
      else {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }

      // Redirection SPA vers /login (PAS de window.location → pas de rechargement),
      // uniquement si on n'y est pas déjà, pour éviter les boucles.
      const current = _router?.currentRoute?.value
      if (current && current.name !== 'login') {
        _router.push({ name: 'login' })
      } else if (!_router && window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  }
)

export default api
