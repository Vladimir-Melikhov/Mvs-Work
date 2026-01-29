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
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
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

    setTokens(tokens) {
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      axios.defaults.headers.common['Authorization'] = `Bearer ${tokens.access}`
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      delete axios.defaults.headers.common['Authorization']
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
        // Добавляем в очередь
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

      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // Нет refresh token - выход
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const response = await axios.post('/api/auth/token/refresh/', {
          refresh: refreshToken
        })

        const { access } = response.data
        localStorage.setItem('access_token', access)
        axios.defaults.headers.common['Authorization'] = `Bearer ${access}`

        processQueue(null, access)
        isRefreshing = false

        originalRequest.headers.Authorization = `Bearer ${access}`
        return axios(originalRequest)

      } catch (refreshError) {
        processQueue(refreshError, null)
        isRefreshing = false

        // Refresh token тоже невалиден - выход
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'

        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
