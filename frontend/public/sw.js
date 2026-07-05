const CACHE_NAME = 'rucher-v2'
const APP_SHELL = ['/']

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)))
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  if (req.method !== 'GET') return

  const url = new URL(req.url)

  // Ne jamais intercepter : l'API, le hot-reload / modules Vite (/@…),
  // ni les requêtes versionnées (?v=, ?t=) du serveur de dev.
  if (
    url.pathname.startsWith('/api') ||
    url.pathname.startsWith('/@') ||
    url.pathname.startsWith('/node_modules') ||
    url.search
  ) {
    return
  }

  // Navigations SPA : réseau d'abord (toujours le code le plus récent),
  // repli sur l'app-shell en cache uniquement hors-ligne.
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('/')))
    return
  }

  // Autres GET same-origin : réseau d'abord, mise en cache best-effort.
  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(req)
        .then((response) => {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone))
          return response
        })
        .catch(() => caches.match(req))
    )
  }
})
