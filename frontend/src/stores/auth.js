import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
    // Tous les rôles attribués par l'admin (options du sélecteur).
    authorizedRoles: (s) => s.user?.roles || [],
    activeRole: (s) => s.user?.active_role || null,
    defaultRole: (s) => s.user?.default_role || null,
    // Rôles EFFECTIFS : limités au rôle actif s'il est sélectionné.
    roles(s) {
      const all = s.user?.roles || []
      const active = s.user?.active_role
      return active && all.includes(active) ? [active] : all
    },
    isAdmin() { return this.roles.includes('admin') },
    isYardManager() { return this.roles.includes('yard_manager') },
    isTreasurer() { return this.roles.includes('treasurer') },
    hasRole() { return (role) => this.roles.includes(role) || this.roles.includes('admin') },
  },
  actions: {
    async login(username, password, remember = true) {
      const { data } = await api.post('/users/login', { username, password, remember })
      this.token = data.access_token
      localStorage.setItem('token', data.access_token)
      await this.fetchUser()
    },
    // Change le rôle actif « à la volée » (nouveau jeton).
    async switchRole(role) {
      const { data } = await api.post('/users/switch-role', { role })
      this.token = data.access_token
      localStorage.setItem('token', data.access_token)
      await this.fetchUser()
    },
    // Définit le rôle actif par défaut (prochaines connexions).
    async setDefaultRole(role) {
      const { data } = await api.put('/users/me/default-role', { role })
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
    },
    async changeMyPassword(currentPassword, newPassword) {
      const { data } = await api.put('/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      // Changer son mot de passe périme les jetons émis auparavant (y compris
      // sur les autres appareils). Le serveur en renvoie un neuf pour cet
      // appareil-ci : sans cela, l'utilisateur se déconnecterait lui-même.
      if (data?.access_token) {
        this.token = data.access_token
        localStorage.setItem('token', data.access_token)
      }
    },
    async fetchUser() {
      const { data } = await api.get('/users/me')
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
