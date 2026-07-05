/**
 * Service de stockage hors-ligne pour les visites (IndexedDB via idb).
 * Expose un compteur réactif `pendingCount` pour l'affichage dans l'UI.
 */
import { openDB } from 'idb'
import { ref } from 'vue'

const DB_NAME = 'rucher-offline'
const STORE = 'pending-visits'

/** Nombre de visites en attente de synchronisation (réactif). */
export const pendingCount = ref(0)

async function getDB() {
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'localId', autoIncrement: true })
      }
    },
  })
}

export async function refreshPendingCount() {
  try {
    const db = await getDB()
    pendingCount.value = await db.count(STORE)
  } catch {
    pendingCount.value = 0
  }
  return pendingCount.value
}

export async function savePendingVisit(visit) {
  const db = await getDB()
  await db.add(STORE, { ...visit, savedAt: new Date().toISOString() })
  await refreshPendingCount()
}

export async function getPendingVisits() {
  const db = await getDB()
  return db.getAll(STORE)
}

export async function clearPendingVisits() {
  const db = await getDB()
  await db.clear(STORE)
  await refreshPendingCount()
}

/**
 * Tente d'envoyer les visites en attente. Renvoie le nombre synchronisé.
 * Sûr à appeler à tout moment (no-op s'il n'y a rien ou si le réseau est absent).
 */
export async function syncPendingVisits(api) {
  const visits = await getPendingVisits()
  if (visits.length === 0) return 0
  try {
    await api.post('/visits/batch', visits)
    await clearPendingVisits()
    return visits.length
  } catch {
    return 0
  }
}
