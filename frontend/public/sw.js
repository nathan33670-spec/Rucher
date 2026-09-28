// Service worker — mode application installée + hors-ligne + notifications push.
// v4 : précache de l'app-shell, cache-first sur les assets hashés (immuables),
// network-first sur la navigation, + gestion des notifications push.
const CACHE = 'rucher-v4'
const SHELL = ['/', '/manifest.json', '/favicon.png', '/icon-192.png', '/icon-512.png', '/apple-touch-icon.png']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {})
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

// ─── Notifications push ─────────────────────────────────────────
self.addEventListener('push', (event) => {
  let data = {}
  try { data = event.data ? event.data.json() : {} } catch (e) { data = { body: event.data && event.data.text() } }
  const title = data.title || 'Rucher'
  const options = {
    body: data.body || '',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [80, 40, 80],
    data: { url: data.url || '/app' },
  }
  event.waitUntil(self.registration.showNotification(title, options))
})

// Le navigateur renouvelle parfois un abonnement push de lui-même : l'ancien
// point de terminaison devient caduc, et l'adhérent cesse de recevoir ses
// notifications sans que rien ne le signale. C'est la cause habituelle des
// abonnements qui « périment » tout seuls. On reprend donc la main ici.
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil((async () => {
    const ancien = event.oldSubscription
    if (!ancien) return
    let nouveau = event.newSubscription
    if (!nouveau) {
      // La clé du serveur est portée par l'ancien abonnement : inutile
      // d'aller la redemander à l'API, qui exigerait un jeton de session
      // auquel le service worker n'a pas accès.
      const options = ancien.options || {}
      try {
        nouveau = await self.registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: options.applicationServerKey,
        })
      } catch (e) {
        return
      }
    }
    const json = nouveau.toJSON()
    try {
      await fetch('/api/notifications/rotate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          old_endpoint: ancien.endpoint,
          endpoint: nouveau.endpoint,
          keys: json.keys,
        }),
      })
    } catch (e) {
      // Sans réseau, le rattrapage au prochain lancement de l'application
      // fera le travail.
    }
  })())
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = (event.notification.data && event.notification.data.url) || '/app'
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const c of list) {
        if ('focus' in c) { c.navigate && c.navigate(url); return c.focus() }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url)
    })
  )
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  if (req.method !== 'GET') return

  const url = new URL(req.url)
  if (url.origin !== self.location.origin) return

  // Jamais de cache pour l'API, le temps réel et les fichiers uploadés.
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/ws') || url.pathname.startsWith('/uploads')) {
    return
  }

  // Assets buildés (nom haché = immuable) → cache d'abord.
  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(
      caches.match(req).then((hit) =>
        hit ||
        fetch(req).then((res) => {
          const clone = res.clone()
          caches.open(CACHE).then((c) => c.put(req, clone))
          return res
        })
      )
    )
    return
  }

  // Navigations SPA → réseau d'abord, repli sur l'app-shell hors-ligne.
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('/')))
    return
  }

  // Autres GET same-origin → réseau d'abord, repli cache.
  event.respondWith(
    fetch(req)
      .then((res) => {
        const clone = res.clone()
        caches.open(CACHE).then((c) => c.put(req, clone))
        return res
      })
      .catch(() => caches.match(req))
  )
})
