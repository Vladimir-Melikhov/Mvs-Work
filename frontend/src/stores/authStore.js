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
        console.error('Registration error:', error)
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
        } else {
          return { 
            success: false, 
            error: response.data.error || 'Login failed' 
          }
        }
      } catch (error) {
        console.error('Login error:', error)
        
        // Обработка разных типов ошибок
        if (error.response) {
          // Сервер ответил с ошибкой
          const errorData = error.response.data
          
          if (error.response.status === 401) {
            return { 
              success: false, 
              error: errorData.error || 'Неверный email или пароль' 
            }
          } else if (error.response.status === 429) {
            return { 
              success: false, 
              error: errorData.error || 'Слишком много попыток. Попробуйте позже.' 
            }
          } else if (error.response.status === 400) {
            return { 
              success: false, 
              error: errorData.error || 'Некорректные данные' 
            }
          } else {
            return { 
              success: false, 
              error: errorData.error || 'Ошибка сервера' 
            }
          }
        } else if (error.request) {
          // Запрос был отправлен, но ответа не получено
          return { 
            success: false, 
            error: 'Нет соединения с сервером' 
          }
        } else {
          // Ошибка при настройке запроса
          return { 
            success: false, 
            error: 'Ошибка при отправке запроса' 
          }
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
        console.error('Update profile error:', error)
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
        } else {
          return {
            success: false,
            error: response.data.error || 'Verification failed'
          }
        }
      } catch (error) {
        console.error('Email verification error:', error)
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
        console.error('Resend verification error:', error)
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
    },

    async deleteAccount(password) {
      try {
        const response = await axios.delete('/api/auth/delete-account/', {
          data: { password },
          headers: { Authorization: `Bearer ${this.accessToken}` },
          withCredentials: true
        })
        
        if (response.data.status === 'success') {
          // Полная очистка состояния и перенаправление
          this.clearAuth()
          this.isInitialized = true
          
          // Принудительный переход на страницу логина
          await router.push('/login')
          
          // Перезагрузка страницы для полной очистки
          window.location.href = '/login'
          
          return { success: true }
        } else {
          return {
            success: false,
            error: response.data.error || 'Ошибка удаления аккаунта'
          }
        }
      } catch (error) {
        console.error('Delete account error:', error)
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
