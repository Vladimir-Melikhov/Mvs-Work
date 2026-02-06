<template>
  <div class="min-h-[80vh] flex items-center justify-center p-6">
    
    <div class="ios-glass-card w-full max-w-[400px] p-8 flex flex-col items-center animate-fade-in">
      
      <h1 class="text-3xl font-bold text-center mb-8 text-[#1a1a2e] drop-shadow-sm tracking-tight">
        С возвращением!
      </h1>

      <div class="w-full space-y-5">
        <div class="relative group">
          <input 
            v-model="email" 
            type="email" 
            placeholder="Почта" 
            class="ios-input"
            @keydown.enter="handleLogin"
            :disabled="isLoading"
          >
        </div>

        <div class="relative group">
          <input 
            v-model="password" 
            type="password" 
            placeholder="Пароль" 
            class="ios-input"
            @keydown.enter="handleLogin"
            :disabled="isLoading"
          >
        </div>

        <div ref="recaptchaContainer" class="flex justify-center"></div>
      </div>

      <div v-if="errorMessage" class="mt-4 p-3 rounded-2xl bg-red-50/80 text-red-500 text-xs font-bold text-center border border-red-100 w-full animate-fade-in">
        {{ errorMessage }}
      </div>
      
      <button @click="handleLogin" :disabled="isLoading" class="ios-button mt-8">
        {{ isLoading ? 'Вход...' : 'Войти' }}
      </button>

      <router-link 
        to="/forgot-password" 
        class="mt-4 text-center text-sm text-gray-500 hover:text-[#7000ff] transition-colors font-medium"
      >
        Забыли пароль?
      </router-link>

      <p class="mt-4 text-center text-gray-500 text-sm font-medium">
        Нет аккаунта? 
        <router-link to="/register" class="text-[#7000ff] font-bold hover:opacity-70 transition-opacity">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)
const recaptchaContainer = ref(null)
let recaptchaWidgetId = null

const auth = useAuthStore()
const router = useRouter()

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY || '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'

const loadRecaptcha = () => {
  return new Promise((resolve) => {
    if (window.grecaptcha) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://www.google.com/recaptcha/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.onload = resolve
    document.head.appendChild(script)
  })
}

const renderRecaptcha = () => {
  if (!recaptchaContainer.value) return

  recaptchaWidgetId = window.grecaptcha.render(recaptchaContainer.value, {
    sitekey: RECAPTCHA_SITE_KEY,
    size: 'normal',
    theme: 'light'
  })
}

const handleLogin = async () => {
  // Сброс ошибки
  errorMessage.value = ''

  // Валидация полей
  if (!email.value || !password.value) {
    errorMessage.value = 'Введите email и пароль'
    return
  }

  // Проверка reCAPTCHA
  const recaptchaToken = window.grecaptcha?.getResponse(recaptchaWidgetId)
  
  if (!recaptchaToken) {
    errorMessage.value = 'Пожалуйста, подтвердите, что вы не робот'
    return
  }

  // Начало загрузки
  isLoading.value = true

  try {
    const res = await auth.login(email.value, password.value, recaptchaToken)
    
    if (res.success) {
      router.push('/')
    } else {
      errorMessage.value = res.error || 'Ошибка входа'
      // Сброс reCAPTCHA при ошибке
      window.grecaptcha.reset(recaptchaWidgetId)
    }
  } catch (error) {
    errorMessage.value = 'Произошла ошибка. Попробуйте снова.'
    window.grecaptcha.reset(recaptchaWidgetId)
  } finally {
    // Завершение загрузки в любом случае
    isLoading.value = false
  }
}

onMounted(async () => {
  await loadRecaptcha()
  
  const checkRecaptcha = setInterval(() => {
    if (window.grecaptcha && window.grecaptcha.render) {
      clearInterval(checkRecaptcha)
      renderRecaptcha()
    }
  }, 100)
})
</script>

<style scoped>
.ios-glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-radius: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.8);
  border-left: 1px solid rgba(255, 255, 255, 0.4);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.1), 
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

.ios-input {
  width: 100%;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.05); 
  border-radius: 20px;
  border: none;
  box-shadow: 
    inset 0 2px 4px rgba(0, 0, 0, 0.05), 
    0 1px 0 rgba(255, 255, 255, 0.5);
  color: #1a1a2e;
  font-size: 16px;
  outline: none;
  transition: all 0.3s ease;
}

.ios-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ios-input::placeholder {
  color: rgba(0, 0, 0, 0.4);
}

.ios-input:focus {
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 
    inset 0 1px 2px rgba(0, 0, 0, 0.05),
    0 0 0 2px rgba(112, 0, 255, 0.1);
}

.ios-button {
  width: 100%;
  padding: 18px;
  border-radius: 24px;
  font-weight: 700;
  font-size: 17px;
  color: white;
  background: #7000ff; 
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 
    0 15px 30px rgba(112, 0, 255, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.2);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.ios-button:hover:not(:disabled) {
  transform: translateY(-2px);
  background: #5b00d1;
}

.ios-button:active {
  transform: scale(0.97);
}

.ios-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.animate-fade-in {
  animation: fade-in 0.6s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
