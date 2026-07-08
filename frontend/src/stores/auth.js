import { defineStore } from 'pinia'
import api from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
    roles: (s) => s.user?.roles || [],
    isAdmin: (s) => s.user?.roles?.includes('admin'),
    isYardManager: (s) => s.user?.roles?.includes('yard_manager'),
    isTreasurer: (s) => s.user?.roles?.includes('treasurer'),
    hasRole: (s) => (role) => s.user?.roles?.includes(role) || s.user?.roles?.includes('admin'),
  },
  actions: {
    async login(username, password) {
      const { data } = await api.post('/users/login', { username, password })
      this.token = data.access_token
      localStorage.setItem('token', data.access_token)
      await this.fetchUser()
    },
    async changeMyPassword(currentPassword, newPassword) {
      await api.put('/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
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
