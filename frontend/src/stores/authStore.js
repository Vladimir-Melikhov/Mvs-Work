import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
  },

  actions: {
    async register(email, password, role = 'client') {
      try {
        const response = await axios.post('/api/auth/register/', {
          email,
          password,
          role
        })
        
        if (response.data.status === 'success') {
          this.setTokens(response.data.data.tokens)
          this.user = response.data.data.user
          return { success: true }
        }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.error || 'Registration failed' 
        }
      }
    },

    async login(email, password) {
      try {
        const response = await axios.post('/api/auth/login/', {
          email,
          password
        })
        
        if (response.data.status === 'success') {
          this.setTokens(response.data.data.tokens)
          this.user = response.data.data.user
          return { success: true }
        }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.error || 'Login failed' 
        }
      }
    },

    async fetchProfile() {
      try {
        const response = await axios.get('/api/auth/profile/', {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        })
        
        if (response.data.status === 'success') {
          this.user = response.data.data
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error)
      }
    },

    setTokens(tokens) {
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }
})