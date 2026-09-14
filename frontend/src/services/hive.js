/**
 * Libellé d'une ruche : le numéro d'abord, le nom en complément.
 *
 * Le numéro est l'identité de la ruche — c'est ce qui est peint sur la caisse
 * et ce qu'on annonce au rucher. Le nom passait avant, si bien qu'une ruche
 * nommée n'affichait jamais son numéro : le modifier ne changeait rien à
 * l'écran, et l'on croyait la modification impossible.
 *
 * La clé primaire n'est jamais affichée : « Ruche #37 » montrait un
 * identifiant technique que personne n'a choisi.
 */
const filled = (v) => v !== null && v !== undefined && String(v).trim() !== ''
const clean = (v) => String(v).trim()

/** Numéro affichable d'une ruche, ou '' si elle n'en a pas encore. */
function numberOf(h) {
  if (filled(h?.number)) return clean(h.number)
  // Base pas encore renumérotée au démarrage : l'ancien champ NAPI servait
  // d'identifiant de ruche. Mieux vaut ce repère que rien.
  if (filled(h?.napi_number)) return clean(h.napi_number)
  return ''
}

export function hiveLabel(h) {
  if (!h) return 'Ruche'
  const num = numberOf(h)
  const nom = filled(h.name) ? clean(h.name) : ''
  if (num && nom) return `${num} — ${nom}`
  if (num) return `Ruche ${num}`
  if (nom) return nom
  return 'Ruche sans numéro'
}

/** Libellé court, pour le plan du rucher où la place manque. */
export function hiveShortLabel(h) {
  if (!h) return '?'
  const num = numberOf(h)
  if (num) return num
  if (filled(h.name)) return clean(h.name)
  return '—'
}

/**
 * Libellé d'une ruche connue seulement par ce qu'en dit le serveur
 * (historique de visite, suivi sanitaire : `hive_name` / `hive_number`).
 */
export function hiveLabelFromRow(row) {
  const num = filled(row?.hive_number) ? clean(row.hive_number) : ''
  const nom = filled(row?.hive_name) ? clean(row.hive_name) : ''
  if (num && nom) return `${num} — ${nom}`
  if (num) return `Ruche ${num}`
  if (nom) return nom
  return 'Ruche sans numéro'
}
