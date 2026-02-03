<template>
    <div class="min-h-screen flex items-center justify-center p-6">
      <div class="ios-glass-card w-full max-w-[420px] p-8 flex flex-col items-center animate-fade-in">
        
        <div class="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center mb-6">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
  
        <h1 class="text-2xl font-bold text-center mb-2 text-[#1a1a2e] tracking-tight">
          Подтвердите email
        </h1>
        
        <p class="text-center text-gray-600 mb-8 text-sm">
          Мы отправили код подтверждения на<br>
          <span class="font-bold text-[#7000ff]">{{ user?.email }}</span>
        </p>
  
        <div class="w-full space-y-4">
          <div class="relative">
            <input 
              v-model="code" 
              type="text" 
              placeholder="Введите 6-значный код" 
              maxlength="6"
              class="ios-input text-center text-2xl tracking-widest font-mono"
              @keydown.enter="verifyCode"
              @input="code = code.replace(/[^0-9]/g, '')"
            >
          </div>
  
          <div v-if="errorMessage" class="p-3 rounded-2xl bg-red-50/80 text-red-500 text-xs font-bold text-center border border-red-100 animate-fade-in">
            {{ errorMessage }}
          </div>
  
          <div v-if="successMessage" class="p-3 rounded-2xl bg-green-50/80 text-green-600 text-xs font-bold text-center border border-green-100 animate-fade-in">
            {{ successMessage }}
          </div>
        </div>
  
        <button 
          @click="verifyCode" 
          :disabled="isLoading || code.length !== 6"
          class="ios-button mt-6"
        >
          {{ isLoading ? 'Проверка...' : 'Подтвердить' }}
        </button>
  
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-500 mb-2">Не получили код?</p>
          <button 
            @click="resendCode"
            :disabled="resendCooldown > 0 || isResending"
            class="text-sm font-bold text-[#7000ff] hover:underline disabled:opacity-50 disabled:no-underline"
          >
            {{ resendCooldown > 0 ? `Отправить повторно (${resendCooldown}с)` : isResending ? 'Отправка...' : 'Отправить повторно' }}
          </button>
        </div>
  
        <button 
          @click="logout" 
          class="mt-8 text-gray-400 hover:text-red-500 text-sm font-bold transition-colors"
        >
          Выйти
        </button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  import { useRouter } from 'vue-router'
  
  const auth = useAuthStore()
  const router = useRouter()
  
  const code = ref('')
  const errorMessage = ref('')
  const successMessage = ref('')
  const isLoading = ref(false)
  const isResending = ref(false)
  const resendCooldown = ref(0)
  
  const user = computed(() => auth.user)
  
  const verifyCode = async () => {
    if (code.value.length !== 6) {
      errorMessage.value = 'Код должен содержать 6 цифр'
      return
    }
  
    errorMessage.value = ''
    successMessage.value = ''
    isLoading.value = true
  
    const result = await auth.verifyEmail(code.value)
  
    if (result.success) {
      successMessage.value = 'Email подтвержден! Перенаправление...'
      setTimeout(() => {
        if (auth.user.role === 'worker' && (!auth.user.profile.skills || auth.user.profile.skills.length === 0)) {
          router.push('/onboarding')
        } else {
          router.push('/')
        }
      }, 1500)
    } else {
      errorMessage.value = result.error || 'Неверный код'
      code.value = ''
    }
  
    isLoading.value = false
  }
  
  const resendCode = async () => {
    if (resendCooldown.value > 0) return
  
    errorMessage.value = ''
    successMessage.value = ''
    isResending.value = true
  
    const result = await auth.resendVerificationCode()
  
    if (result.success) {
      successMessage.value = 'Код отправлен повторно!'
      resendCooldown.value = 60
      
      const interval = setInterval(() => {
        resendCooldown.value--
        if (resendCooldown.value <= 0) {
          clearInterval(interval)
        }
      }, 1000)
    } else {
      errorMessage.value = result.error || 'Не удалось отправить код'
    }
  
    isResending.value = false
  }
  
  const logout = () => {
    auth.logout()
    router.push('/login')
  }
  
  onMounted(() => {
    if (!auth.user) {
      router.push('/login')
    } else if (auth.user.email_verified) {
      router.push('/')
    }
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
    outline: none;
    transition: all 0.3s ease;
  }
  
  .ios-input:focus {
    background: rgba(255, 255, 255, 0.5);
    box-shadow: 
      inset 0 1px 2px rgba(0, 0, 0, 0.05),
      0 0 0 4px rgba(112, 0, 255, 0.05);
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
      0 12px 24px rgba(112, 0, 255, 0.3),
      inset 0 2px 0 rgba(255, 255, 255, 0.2);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
  }
  
  .ios-button:hover:not(:disabled) {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }
  
  .ios-button:active:not(:disabled) {
    transform: scale(0.97);
  }
  
  .ios-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: #a8a8a8;
    box-shadow: none;
  }
  
  .animate-fade-in {
    animation: fade-in 0.3s ease-out;
  }
  
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  </style>
  