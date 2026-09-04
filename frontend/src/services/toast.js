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

/**
 * Traduit une erreur axios en un message que l'utilisateur peut comprendre
 * — et sur lequel il peut agir.
 *
 * Auparavant chaque vue affichait « Erreur » : ni la cause, ni ce qu'il
 * fallait corriger. On distingue désormais la perte de réseau, la session
 * expirée, le manque de droits, la saisie invalide et la panne serveur (qui
 * porte une référence à citer à l'administrateur).
 */
export function apiError(e, fallback = 'Une erreur est survenue') {
  // Pas de réponse du tout : réseau coupé, serveur injoignable ou requête annulée.
  if (e && !e.response) {
    if (e.code === 'ECONNABORTED') return "Le serveur met trop de temps à répondre. Réessayez."
    if (typeof navigator !== 'undefined' && navigator.onLine === false)
      return "Vous êtes hors connexion : la modification n'a pas été envoyée."
    return "Serveur injoignable. Vérifiez votre connexion, puis réessayez."
  }

  const status = e?.response?.status
  const detail = e?.response?.data?.detail

  // Le serveur a formulé un message : c'est toujours le plus précis.
  if (typeof detail === 'string' && detail.trim()) return detail
  // Erreurs de validation brutes (schéma FastAPI par défaut).
  if (Array.isArray(detail) && detail.length) {
    const lines = detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc.filter((x) => x !== 'body').join(' → ') : ''
        return field ? `${field} : ${d.msg}` : d.msg
      })
      .filter(Boolean)
    if (lines.length) return 'Saisie invalide — ' + lines.slice(0, 3).join(' · ')
  }

  switch (status) {
    case 400: return "Demande invalide : vérifiez les informations saisies."
    case 401: return "Votre session a expiré. Reconnectez-vous."
    case 403: return "Vous n'avez pas les droits nécessaires pour cette action."
    case 404: return "Élément introuvable : il a peut-être été supprimé entre-temps."
    case 409: return "Conflit : cet enregistrement existe déjà ou est encore utilisé ailleurs."
    case 413: return "Fichier trop volumineux."
    case 422: return "Saisie incomplète ou invalide : vérifiez les champs du formulaire."
    case 429: return "Trop de requêtes : patientez quelques instants."
    case 500: return "Erreur interne du serveur. Réessayez, puis prévenez l'administrateur."
    case 502:
    case 503:
    case 504: return "Le serveur est momentanément indisponible. Réessayez dans un instant."
    default: return fallback
  }
}
