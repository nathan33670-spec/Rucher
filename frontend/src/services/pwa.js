/**
 * Gestion de l'installation PWA (« ajouter à l'écran d'accueil »).
 *
 * - Android / Chrome / Edge : capture l'événement `beforeinstallprompt` et
 *   permet de déclencher l'invite native.
 * - iOS / Safari : pas d'API d'installation → on détecte iOS pour afficher des
 *   instructions manuelles (Partager → Sur l'écran d'accueil).
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

/** Vrai si l'app peut être installée (invite dispo, ou iOS via Partager). */
export const canInstall = computed(
  () => !installed.value && (!!deferredPrompt.value || isIOS)
)

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

/** Déclenche l'invite native. Renvoie true si l'utilisateur a accepté. */
export async function promptInstall() {
  const e = deferredPrompt.value
  if (!e) return false
  e.prompt()
  const { outcome } = await e.userChoice
  deferredPrompt.value = null
  return outcome === 'accepted'
}
