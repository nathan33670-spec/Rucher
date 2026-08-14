/**
 * Formatage homogène des valeurs affichées dans l'application.
 *
 * Utilise l'API Intl du navigateur pour respecter les conventions
 * françaises : virgule décimale, espace insécable avant le symbole €
 * et séparateur de milliers (1 250,00 € plutôt que 1250.00 €).
 */

const eur = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const num = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 })

/** Montant en euros. Renvoie « — » si la valeur est absente. */
export function money(value, dash = '—') {
  if (value === null || value === undefined || value === '') return dash
  const n = Number(value)
  return Number.isFinite(n) ? eur.format(n) : dash
}

/** Nombre décimal (poids, quantités…). */
export function decimal(value, dash = '—') {
  if (value === null || value === undefined || value === '') return dash
  const n = Number(value)
  return Number.isFinite(n) ? num.format(n) : dash
}

/** Date courte : 14/08/2026. */
export function shortDate(value, dash = '—') {
  if (!value) return dash
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? dash : d.toLocaleDateString('fr-FR')
}
