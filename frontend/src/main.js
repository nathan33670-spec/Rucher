import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import './styles/app.css'
import { attachRouter, MODE_DEMO, demoPrete } from './services/api'
import { setupPwa } from './services/pwa'

// Capture l'événement d'installation PWA au plus tôt (avant le montage).
setupPwa()

/**
 * Démarrage de l'application.
 *
 * En démonstration publique, deux choses doivent être en place **avant**
 * d'installer le routeur : l'API simulée, et la session ouverte d'office.
 * Installer le routeur déclenche aussitôt la résolution de la première
 * navigation, donc le garde d'authentification — qui renvoyait vers l'écran
 * de connexion parce que la session n'était pas encore écrite.
 */
async function demarrer() {
  if (MODE_DEMO) {
    const utilisateur = await demoPrete
    if (utilisateur) {
      // Le jeton seul ne suffit pas : les gardes de route lisent les rôles.
      // Demander un mot de passe pour une démonstration publique ne
      // protégerait rien et ferait fuir la moitié des visiteurs.
      localStorage.setItem('token', 'demo')
      localStorage.setItem('user', JSON.stringify(utilisateur))
    }
  }

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(vuetify)

  // Permet à l'intercepteur axios de rediriger via le router (navigation SPA,
  // sans rechargement complet de la page) en cas de session expirée.
  attachRouter(router)

  app.mount('#app')
}

demarrer()

// Service worker : il sert le mode hors-ligne de l'application réelle. Dans la
// démonstration il n'a rien d'utile à mettre en cache, et son cache survivrait
// aux mises à jour de la page — on ne l'enregistre donc pas.
if ('serviceWorker' in navigator && !MODE_DEMO) {
  navigator.serviceWorker.register(import.meta.env.BASE_URL + 'sw.js').catch(() => {})
}
