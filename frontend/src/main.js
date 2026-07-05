import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { attachRouter } from './services/api'
import { setupPwa } from './services/pwa'

// Capture l'événement d'installation PWA au plus tôt (avant le montage).
setupPwa()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(vuetify)

// Permet à l'intercepteur axios de rediriger via le router (navigation SPA,
// sans rechargement complet de la page) en cas de session expirée.
attachRouter(router)

app.mount('#app')

// Enregistrer le service worker pour le mode offline
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {})
}
