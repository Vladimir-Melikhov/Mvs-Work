<template>
    <div class="min-h-[80vh] flex items-center justify-center p-6">
      <div class="ios-glass-card w-full max-w-[400px] p-8 flex flex-col items-center animate-fade-in">
        
        <div class="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center mb-6">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        </div>
        
        <h1 class="text-3xl font-bold text-center mb-2 text-[#1a1a2e] drop-shadow-sm tracking-tight">
          Забыли пароль?
        </h1>
        
        <p class="text-center text-gray-600 mb-8 text-sm">
          Введите ваш email, и мы отправим ссылку для сброса пароля
        </p>
  
        <div class="w-full space-y-5">
          <div class="relative group">
            <input 
              v-model="email" 
              type="email" 
              placeholder="Ваш email" 
              class="ios-input"
              @keydown.enter="handleSubmit"
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
          {{ isLoading ? 'Отправка...' : 'Отправить ссылку' }}
        </button>
  
        <router-link 
          to="/login" 
          class="mt-6 text-center text-gray-500 text-sm font-medium hover:text-[#7000ff] transition-colors"
        >
          Вернуться ко входу
        </router-link>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  
  const email = ref('')
  const errorMessage = ref('')
  const successMessage = ref('')
  const isLoading = ref(false)
  
  const handleSubmit = async () => {
    errorMessage.value = ''
    successMessage.value = ''
    
    if (!email.value) {
      errorMessage.value = 'Введите email'
      return
    }
    
    isLoading.value = true
    
    try {
      const response = await axios.post('/api/auth/forgot-password/', {
        email: email.value
      })
      
      if (response.data.status === 'success') {
        successMessage.value = response.data.message || 'Ссылка для сброса пароля отправлена на email'
        email.value = ''
      }
    } catch (error) {
      errorMessage.value = error.response?.data?.error || 'Произошла ошибка'
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
  