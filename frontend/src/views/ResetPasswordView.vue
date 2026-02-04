<!-- frontend/src/views/ResetPasswordView.vue -->
<template>
    <div class="min-h-[80vh] flex items-center justify-center p-6">
      <div class="ios-glass-card w-full max-w-[400px] p-8 flex flex-col items-center animate-fade-in">
        
        <div class="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center mb-6">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        
        <h1 class="text-3xl font-bold text-center mb-2 text-[#1a1a2e] drop-shadow-sm tracking-tight">
          Новый пароль
        </h1>
        
        <p class="text-center text-gray-600 mb-8 text-sm">
          Введите новый пароль для вашего аккаунта
        </p>
  
        <div class="w-full space-y-5">
          <div class="relative group">
            <input 
              v-model="password" 
              type="password" 
              placeholder="Новый пароль (минимум 6 символов)" 
              class="ios-input"
            >
          </div>
          
          <div class="relative group">
            <input 
              v-model="confirmPassword" 
              type="password" 
              placeholder="Повторите пароль" 
              class="ios-input"
              @keydown.enter="handleSubmit"
              :class="{'border-2 border-red-400 bg-red-50/50': password && confirmPassword && password !== confirmPassword}"
            >
          </div>
        </div>
  
        <div v-if="errorMessage" class="mt-4 p-3 rounded-2xl bg-red-50/80 text-red-500 text-xs font-bold text-center border border-red-100 w-full animate-fade-in">
          {{ errorMessage }}
        </div>
        
        <div v-if="successMessage" class="mt-4 p-3 rounded-2xl bg-green-50/80 text-green-600 text-xs font-bold text-center border border-green-100 w-full animate-fade-in">
          {{ successMessage }}
        </div>
        
        <button 
          @click="handleSubmit" 
          :disabled="isLoading"
          class="ios-button mt-8"
        >
          {{ isLoading ? 'Сохранение...' : 'Сохранить пароль' }}
        </button>
  
        <router-link 
          v-if="successMessage"
          to="/login" 
          class="mt-6 text-center text-[#7000ff] text-sm font-bold hover:underline"
        >
          Перейти ко входу
        </router-link>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import axios from 'axios'
  
  const route = useRoute()
  const router = useRouter()
  
  const password = ref('')
  const confirmPassword = ref('')
  const errorMessage = ref('')
  const successMessage = ref('')
  const isLoading = ref(false)
  const token = ref('')
  
  onMounted(() => {
    token.value = route.query.token || ''
    
    if (!token.value) {
      errorMessage.value = 'Отсутствует токен сброса пароля'
    }
  })
  
  const handleSubmit = async () => {
    errorMessage.value = ''
    successMessage.value = ''
    
    if (!password.value) {
      errorMessage.value = 'Введите новый пароль'
      return
    }
    
    if (password.value.length < 6) {
      errorMessage.value = 'Пароль должен быть не менее 6 символов'
      return
    }
    
    if (password.value !== confirmPassword.value) {
      errorMessage.value = 'Пароли не совпадают'
      return
    }
    
    if (!token.value) {
      errorMessage.value = 'Отсутствует токен сброса пароля'
      return
    }
    
    isLoading.value = true
    
    try {
      const response = await axios.post('/api/auth/reset-password/', {
        token: token.value,
        new_password: password.value
      })
      
      if (response.data.status === 'success') {
        successMessage.value = 'Пароль успешно изменен! Теперь вы можете войти с новым паролем.'
        password.value = ''
        confirmPassword.value = ''
        
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      }
    } catch (error) {
      errorMessage.value = error.response?.data?.error || 'Произошла ошибка при сбросе пароля'
    } finally {
      isLoading.value = false
    }
  }
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