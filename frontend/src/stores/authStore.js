// frontend/src/stores/authStore.js
import { defineStore } from 'pinia'
import axios from 'axios'

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: null,  // ✅ Только в памяти
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    isWorker: (state) => state.user?.role === 'worker'
  },

  actions: {
    async register(email, password, role = 'client') {
      try {
        const response = await axios.post('/api/auth/register/', {
          email,
          password,
          role
        }, {
          withCredentials: true
        })
        
        if (response.data.status === 'success') {
          this.accessToken = response.data.data.tokens.access
          this.user = response.data.data.user
          
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
          
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
        }, {
          withCredentials: true
        })
        
        if (response.data.status === 'success') {
          this.accessToken = response.data.data.tokens.access
          this.user = response.data.data.user
          
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
          
          return { success: true }
        }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.error || 'Login failed' 
        }
      }
    },

    async updateProfile(profileData) {
        try {
            const response = await axios.patch('/api/auth/profile/', profileData, {
                headers: { Authorization: `Bearer ${this.accessToken}` }
            })

            if (response.data.status === 'success') {
                this.user = response.data.data
                return { success: true }
            }
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Update failed'
            }
        }
    },

    async fetchProfile() {
      try {
        if (!this.accessToken) return
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

    async refreshAccessToken() {
      try {
        const response = await axios.post('/api/auth/token/refresh/', {}, {
          withCredentials: true
        })
        
        if (response.data && response.data.access) {
          this.accessToken = response.data.access
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
          return true
        }
        
        return false
      } catch (error) {
        console.error('Token refresh failed:', error)
        this.logout()
        return false
      }
    },

    async initAuth() {
      try {
        await this.refreshAccessToken()
        if (this.accessToken) {
          await this.fetchProfile()
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.accessToken = null
      delete axios.defaults.headers.common['Authorization']
      
      document.cookie = 'refresh_token=; Max-Age=0; path=/;'
    }
  }
})

// Axios interceptor для автоматического refresh токена
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return axios(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const authStore = useAuthStore()

      try {
        const success = await authStore.refreshAccessToken()
        
        if (success) {
          processQueue(null, authStore.accessToken)
          originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
          return axios(originalRequest)
        } else {
          processQueue(error, null)
          return Promise.reject(error)
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        authStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)
