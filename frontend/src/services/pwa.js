/**
 * Gestion de l'installation PWA (« ajouter à l'écran d'accueil »).
 *
 * On propose l'installation DÈS QUE l'app n'est pas déjà installée, sans dépendre
 * uniquement de l'événement `beforeinstallprompt` (qui n'est pas toujours émis
 * immédiatement par Chrome, et jamais par iOS Safari) :
 *  - si l'invite native est disponible → on la déclenche ;
 *  - sinon → on affiche des instructions manuelles adaptées (Android/desktop ou iOS).
 */
import { ref, computed } from 'vue'

export const deferredPrompt = ref(null)
export const installed = ref(isStandalone())

export const isIOS =
  /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream

function isStandalone() {
  return (
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  )
}

/** Invite native disponible (Android/Chrome/Edge, après émission de l'événement). */
export const promptAvailable = computed(() => !!deferredPrompt.value)

/** On propose l'installation tant que l'app n'est pas installée. */
export const canInstall = computed(() => !installed.value)

/** À appeler une fois au démarrage (dans main.js). */
export function setupPwa() {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredPrompt.value = e
  })
  window.addEventListener('appinstalled', () => {
    installed.value = true
    deferredPrompt.value = null
  })
}

/** Déclenche l'invite native si dispo. Renvoie true si acceptée. */
export async function promptInstall() {
  const e = deferredPrompt.value
  if (!e) return false
  e.prompt()
  const { outcome } = await e.userChoice
  deferredPrompt.value = null
  return outcome === 'accepted'
}
