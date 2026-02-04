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
        }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.error || 'Registration failed' 
        }
      }
    },

    async login(email, password, recaptchaToken) {
      try {
        const response = await axios.post('/api/auth/login/', {
          email,
          password,
          recaptcha_token: recaptchaToken
        }, {
          withCredentials: true
        })
        
        if (response.data.status === 'success') {
          this.accessToken = response.data.data.tokens.access
          this.user = response.data.data.user
          this.isInitialized = true
          
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
        throw error
      }
    },

    async refreshAccessToken() {
      try {
        console.log('🔄 Refreshing token...')
        console.log('📨 Cookies:', document.cookie)
        
        const response = await axios.post('/api/auth/token/refresh/', {}, {
          withCredentials: true
        })
        
        console.log('✅ Refresh response:', response.data)
        
        if (response.data && response.data.access) {
          this.accessToken = response.data.access
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
          return true
        }
        
        console.warn('⚠️ No access token in response')
        return false
      } catch (error) {
        console.error('❌ Token refresh failed:', error.response?.data || error.message)
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
        console.error('Auth initialization failed:', error)
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
        console.error('Logout error:', error)
      } finally {
        this.clearAuth()
        this.isInitialized = true
        router.push('/login')
      }
    }
  }
})

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