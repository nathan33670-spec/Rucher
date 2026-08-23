// Messages transitoires de l'application (remplace alert() natif et les
// snackbars recopiés dans chaque vue).
//
// Usage :  toastError('Enregistrement impossible')
//          toastSuccess('Visite enregistrée')
import { reactive } from 'vue'

export const toastState = reactive({
  open: false,
  message: '',
  color: 'success',
  timeout: 3000,
})

function show(message, color, timeout) {
  if (!message) return
  // Réouvrir force le remplacement du message précédent plutôt que de
  // laisser deux notifications se chevaucher.
  toastState.open = false
  toastState.message = message
  toastState.color = color
  toastState.timeout = timeout
  toastState.open = true
}

export function toastSuccess(message) { show(message, 'success', 2500) }
export function toastError(message) { show(message, 'error', 5000) }
export function toastInfo(message) { show(message, 'info', 3500) }

/** Extrait le message utile d'une erreur axios, avec un repli lisible. */
export function apiError(e, fallback = 'Une erreur est survenue') {
  return e?.response?.data?.detail || fallback
}
