// Boîte de confirmation réutilisable (remplace confirm() natif).
// Usage :  if (!(await confirmAction('Supprimer ceci ?'))) return
import { reactive } from 'vue'

export const confirmState = reactive({
  open: false,
  title: 'Confirmer',
  message: '',
  confirmText: 'Supprimer',
  color: 'error',
  _resolve: null,
})

export function confirmAction(message, opts = {}) {
  confirmState.message = message
  confirmState.title = opts.title || 'Confirmer'
  confirmState.confirmText = opts.confirmText || 'Supprimer'
  confirmState.color = opts.color || 'error'
  confirmState.open = true
  return new Promise((resolve) => { confirmState._resolve = resolve })
}

export function resolveConfirm(value) {
  confirmState.open = false
  const r = confirmState._resolve
  confirmState._resolve = null
  if (r) r(value)
}
