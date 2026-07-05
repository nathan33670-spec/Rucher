/**
 * Service de stockage hors-ligne pour les visites (IndexedDB via idb).
 */
import { openDB } from 'idb'

const DB_NAME = 'rucher-offline'
const STORE = 'pending-visits'

async function getDB() {
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'localId', autoIncrement: true })
      }
    },
  })
}

export async function savePendingVisit(visit) {
  const db = await getDB()
  await db.add(STORE, { ...visit, savedAt: new Date().toISOString() })
}

export async function getPendingVisits() {
  const db = await getDB()
  return db.getAll(STORE)
}

export async function clearPendingVisits() {
  const db = await getDB()
  await db.clear(STORE)
}

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
