import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

/**
 * Centre de notifications (icône cloche).
 *
 * Les notifications vivent côté serveur : elles survivent au rechargement de
 * la page, se retrouvent sur tous les appareils, et restent consultables même
 * quand le push n'est pas activé — c'est justement ce qui manquait, la liste
 * n'existait qu'en mémoire du navigateur.
 *
 * `localAlerts` complète la liste pour ce qui est saisi hors connexion : la
 * notification serveur n'existera qu'après synchronisation.
 */
export const useNotifStore = defineStore('notif', () => {
  const messages = ref([])
  const localAlerts = ref([])
  const loading = ref(false)
  const loaded = ref(false)

  const alerts = computed(() => [...localAlerts.value, ...messages.value])
  const unread = computed(
    () => localAlerts.value.filter((a) => !a.read).length
      + messages.value.filter((m) => !m.read).length,
  )

  async function load() {
    loading.value = true
    try {
      const { data } = await api.get('/notifications/inbox', { params: { limit: 50 } })
      messages.value = data.messages || []
      loaded.value = true
    } catch {
      // Hors connexion ou session expirée : on garde ce qu'on a déjà.
    } finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    const local = localAlerts.value.find((a) => a.id === id)
    if (local) { local.read = true; return }
    const m = messages.value.find((x) => x.id === id)
    if (!m || m.read) return
    m.read = true
    try { await api.post(`/notifications/inbox/${id}/read`) } catch { m.read = false }
  }

  async function markAllRead() {
    localAlerts.value.forEach((a) => { a.read = true })
    const previously = messages.value.map((m) => m.read)
    messages.value.forEach((m) => { m.read = true })
    try {
      await api.post('/notifications/inbox/read-all')
    } catch {
      messages.value.forEach((m, i) => { m.read = previously[i] })
    }
  }

  async function clearAll() {
    localAlerts.value = []
    const previous = messages.value
    messages.value = []
    try { await api.delete('/notifications/inbox') } catch { messages.value = previous }
  }

  /** Alerte purement locale (visite enregistrée hors connexion). */
  function addAlert(alert) {
    localAlerts.value.unshift({
      id: 'local-' + Date.now(),
      category: 'alerts',
      title: alert.title || alert.message,
      body: alert.body || (alert.hiveName ? `${alert.hiveName} — ${alert.date}` : ''),
      created_at: new Date().toISOString(),
      local: true,
      read: false,
    })
  }

  return { messages, localAlerts, alerts, unread, loading, loaded,
           load, markRead, markAllRead, clearAll, addAlert }
})
