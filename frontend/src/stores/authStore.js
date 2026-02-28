import { defineStore } from 'pinia'
import axios from 'axios'
import router from '../router'

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
    accessToken: null,
    isInitialized: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
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
          this.isInitialized = true
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
          return { success: true }
        } else {
          return { 
            success: false, 
            error: response.data.error || 'Registration failed' 
          }
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
          this.isInitialized = true
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
          return { success: true }
        } else {
          return { 
            success: false, 
            error: response.data.error || 'Ошибка входа. Проверьте данные и попробуйте снова.' 
          }
        }
      } catch (error) {
        if (error.response) {
          if (error.response.status === 401) {
            return { success: false, error: 'Неверный email или пароль' }
          } else if (error.response.status === 429) {
            return { success: false, error: 'Слишком много попыток. Попробуйте позже.' }
          } else if (error.response.status === 400) {
            return { success: false, error: error.response.data.error || 'Некорректные данные' }
          } else {
            return { success: false, error: 'Ошибка сервера. Попробуйте позже.' }
          }
        } else if (error.request) {
          return { success: false, error: 'Нет соединения с сервером' }
        } else {
          return { success: false, error: 'Ошибка входа. Проверьте данные и попробуйте снова.' }
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
        } else {
          return {
            success: false,
            error: response.data.error || 'Update failed'
          }
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
        throw error
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
        this.clearAuth()
        return false
      }
    },

    async initAuth() {
      try {
        const success = await this.refreshAccessToken()
        if (success) {
          await this.fetchProfile()
        }
      } catch (error) {
        this.clearAuth()
      } finally {
        this.isInitialized = true
      }
    },

    async verifyEmail(code) {
      try {
        const response = await axios.post('/api/auth/verify-email/', {
          code
        }, {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        })
        
        if (response.data.status === 'success') {
          this.user.email_verified = true
          return { success: true }
        } else {
          return {
            success: false,
            error: response.data.error || 'Verification failed'
          }
        }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || 'Verification failed'
        }
      }
    },

    async resendVerificationCode() {
      try {
        const response = await axios.post('/api/auth/resend-verification/', {}, {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        })
        
        if (response.data.status === 'success') {
          return { success: true }
        } else {
          return {
            success: false,
            error: response.data.error || 'Failed to resend code'
          }
        }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || 'Failed to resend code'
        }
      }
    },

    clearAuth() {
      this.user = null
      this.accessToken = null
      delete axios.defaults.headers.common['Authorization']
    },

    async logout() {
      try {
        await axios.post('/api/auth/logout/', {}, {
          headers: { Authorization: `Bearer ${this.accessToken}` },
          withCredentials: true
        })
      } catch (error) {
        // silent
      } finally {
        this.clearAuth()
        this.isInitialized = true
        router.push('/login')
      }
    },

    async deleteAccount(password) {
      try {
        const response = await axios.delete('/api/auth/delete-account/', {
          data: { password },
          headers: { Authorization: `Bearer ${this.accessToken}` },
          withCredentials: true
        })
        
        if (response.data.status === 'success') {
          this.clearAuth()
          this.isInitialized = true
          await router.push('/login')
          window.location.href = '/login'
          return { success: true }
        } else {
          return {
            success: false,
            error: response.data.error || 'Ошибка удаления аккаунта'
          }
        }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || 'Ошибка удаления аккаунта'
        }
      }
    }
  }
})

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    const authEndpoints = [
      '/api/auth/login/',
      '/api/auth/register/',
      '/api/auth/token/refresh/',
      '/api/auth/forgot-password/',
      '/api/auth/reset-password/'
    ]

    const isAuthEndpoint = authEndpoints.some(endpoint => 
      originalRequest.url?.includes(endpoint)
    )

    if (isAuthEndpoint) {
      return Promise.reject(error)
    }

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
          authStore.clearAuth()
          router.push('/login')
          return Promise.reject(error)
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        authStore.clearAuth()
        router.push('/login')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)