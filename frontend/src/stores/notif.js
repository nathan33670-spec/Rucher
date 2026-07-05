import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotifStore = defineStore('notif', () => {
  const alerts = ref([])

  function addAlert(alert) {
    alerts.value.unshift({ ...alert, id: Date.now(), read: false })
  }
  function markRead(id) {
    const a = alerts.value.find((x) => x.id === id)
    if (a) a.read = true
  }
  function clearAll() {
    alerts.value = []
  }

  return { alerts, addAlert, markRead, clearAll }
})
