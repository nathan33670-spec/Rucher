/**
 * Libellé d'une ruche, sans jamais exposer sa clé primaire.
 *
 * Afficher « Ruche #37 » revenait à montrer l'identifiant technique de la base :
 * un numéro que personne n'a choisi, qu'on ne peut pas modifier, et qui ne
 * correspond à rien sur le terrain. On affiche donc le nom, sinon le numéro
 * choisi, sinon l'ancien champ NAPI (les bases antérieures y rangeaient
 * l'identifiant de la ruche).
 */
const filled = (v) => v !== null && v !== undefined && String(v).trim() !== ''

export function hiveLabel(h) {
  if (!h) return 'Ruche'
  if (filled(h.name)) return String(h.name).trim()
  if (filled(h.number)) return 'Ruche ' + String(h.number).trim()
  if (filled(h.napi_number)) return 'Ruche ' + String(h.napi_number).trim()
  return 'Ruche sans numéro'
}

/** Libellé court, pour le plan du rucher où la place manque. */
export function hiveShortLabel(h) {
  if (!h) return '?'
  if (filled(h.number)) return String(h.number).trim()
  if (filled(h.napi_number)) return String(h.napi_number).trim()
  if (filled(h.name)) return String(h.name).trim()
  return '—'
}

/**
 * Libellé d'une ruche connue seulement par ce qu'en dit le serveur
 * (historique de visite, suivi sanitaire : `hive_name` / `hive_number`).
 */
export function hiveLabelFromRow(row) {
  if (filled(row?.hive_name)) return String(row.hive_name).trim()
  if (filled(row?.hive_number)) return 'Ruche ' + String(row.hive_number).trim()
  return 'Ruche sans numéro'
}
