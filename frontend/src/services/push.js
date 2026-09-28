/**
 * Notifications push web (côté client).
 * S'appuie sur le service worker déjà enregistré (main.js) + l'API backend.
 */
import api from './api'

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  const arr = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i)
  return arr
}

export const pushSupported = () =>
  'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window

export const isStandalone = () =>
  window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true

export const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream

/** État courant de l'abonnement sur cet appareil. */
export async function getPushState() {
  if (!pushSupported()) return { supported: false, subscribed: false, permission: 'unsupported' }
  const reg = await navigator.serviceWorker.ready
  const sub = await reg.pushManager.getSubscription()
  return { supported: true, subscribed: !!sub, permission: Notification.permission }
}

/** Demande la permission, s'abonne et enregistre l'abonnement côté serveur. */
export async function enablePush() {
  if (!pushSupported()) throw new Error('Notifications non supportées sur cet appareil.')
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') throw new Error('Permission refusée.')
  const reg = await navigator.serviceWorker.ready
  let sub = await reg.pushManager.getSubscription()
  if (!sub) {
    const { data } = await api.get('/notifications/vapid-public-key')
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(data.publicKey),
    })
  }
  const json = sub.toJSON()
  await api.post('/notifications/subscribe', { endpoint: sub.endpoint, keys: json.keys })
  return true
}

/**
 * Ré-enregistre l'abonnement de cet appareil côté serveur (auto-réparation).
 *
 * Deux cas sont rattrapés :
 *  - le navigateur a un abonnement que le serveur ignore (créé pendant une
 *    panne de /subscribe) ;
 *  - le navigateur n'en a plus du tout, alors que la permission est toujours
 *    accordée. C'est le cas qui faisait « périmer » les notifications :
 *    l'abonnement disparaissait à l'occasion d'un nettoyage du navigateur ou
 *    d'une mise à jour, et il fallait le rétablir à la main dans les
 *    réglages, sans le moindre message pour le dire.
 *
 * /subscribe fait un upsert : l'appel est idempotent.
 */
export async function resyncSubscription() {
  if (!pushSupported()) return false
  const reg = await navigator.serviceWorker.ready
  let sub = await reg.pushManager.getSubscription()
  if (!sub) {
    // Ne jamais demander la permission ici : on ne fait que rétablir un
    // consentement déjà donné, en silence.
    if (Notification.permission !== 'granted') return false
    try {
      const { data } = await api.get('/notifications/vapid-public-key')
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(data.publicKey),
      })
    } catch (e) {
      return false
    }
  }
  const json = sub.toJSON()
  await api.post('/notifications/subscribe', { endpoint: sub.endpoint, keys: json.keys })
  return true
}

/** Désabonne cet appareil. */
export async function disablePush() {
  if (!pushSupported()) return
  const reg = await navigator.serviceWorker.ready
  const sub = await reg.pushManager.getSubscription()
  if (sub) {
    await api.post('/notifications/unsubscribe', { endpoint: sub.endpoint }).catch(() => {})
    await sub.unsubscribe().catch(() => {})
  }
}

export async function getPrefs() {
  const { data } = await api.get('/notifications/preferences')
  return data
}
/** Catégories réservées auxquelles ce compte a droit. */
export async function getCapabilities() {
  const { data } = await api.get('/notifications/preferences/capabilities')
  return data
}
export async function setPrefs(partial) {
  const { data } = await api.put('/notifications/preferences', partial)
  return data
}
export async function sendTest() {
  const { data } = await api.post('/notifications/test')
  return data
}
