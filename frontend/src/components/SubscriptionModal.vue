<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in backdrop-blur-sm bg-black/10">
      <div class="absolute inset-0" @click="$emit('close')"></div>
      
      <div class="ios-glass-card relative w-full max-w-[400px] p-8 flex flex-col items-center overflow-hidden">
        <div class="absolute -top-24 -right-24 w-48 h-48 bg-[#7000ff]/10 blur-[60px] rounded-full"></div>
  
        <button 
          @click="$emit('close')" 
          class="absolute top-5 right-5 w-8 h-8 flex items-center justify-center rounded-full bg-black/5 hover:bg-black/10 transition-colors"
        >
          <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
  
        <div class="w-16 h-16 ios-icon-lens mb-6 flex items-center justify-center">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
  
        <h2 class="text-2xl font-bold text-[#1a1a2e] tracking-tight mb-2">Подписка</h2>
        <p class="text-sm text-gray-500 font-medium text-center mb-8">Откройте доступ к заказам и публикациям без ограничений</p>
  
        <div class="ios-inset-box w-full py-6 mb-8 flex flex-col items-center">
          <div class="flex items-baseline gap-1">
            <span class="text-5xl font-black text-[#1a1a2e] tracking-tighter">444</span>
            <span class="text-xl font-bold text-[#1a1a2e]/60">₽</span>
          </div>
          <p class="text-[10px] uppercase tracking-[0.2em] font-black text-gray-400 mt-1">ежемесячно</p>
        </div>
  
        <div class="w-full space-y-4 mb-8">
          <div v-for="text in features" :key="text" class="flex items-center gap-3">
            <div class="w-5 h-5 rounded-full bg-[#7000ff]/10 flex items-center justify-center shrink-0">
              <svg class="w-3 h-3 text-[#7000ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span class="text-sm font-medium text-gray-600">{{ text }}</span>
          </div>
        </div>
  
        <button @click="subscribe" :disabled="loading" class="ios-button">
          {{ loading ? 'Обработка...' : 'Подключить сейчас' }}
        </button>
  
        <p class="mt-4 text-[10px] text-gray-400 font-medium">Отмена в любое время в настройках профиля</p>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  
  const emit = defineEmits(['close', 'subscribed'])
  const loading = ref(false)
  
  const features = [
    'Работа без ограничений',
    'Нулевая комиссия сервиса',
    'Дешевле стакана кофе'
  ]
  
  const subscribe = async () => {
    try {
      loading.value = true
      const response = await axios.post('/api/auth/subscription/')
      if (response.data.status === 'success') {
        emit('subscribed')
      }
    } catch (err) {
      console.error('Subscription failed:', err)
      alert('Ошибка при оплате подписки')
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <style scoped>
  .ios-glass-card {
    /* Фон карточки изменен с 0.4 на 0.6 для более "чистого" белого стекла */
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(30px) saturate(180%);
    -webkit-backdrop-filter: blur(30px) saturate(180%);
    border-radius: 44px;
    
    border-top: 1px solid rgba(255, 255, 255, 0.7);
    border-left: 1px solid rgba(255, 255, 255, 0.4);
    border-right: 1px solid rgba(255, 255, 255, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    
    box-shadow: 
      0 40px 80px rgba(0, 0, 0, 0.1), 
      inset 0 0 0 1px rgba(255, 255, 255, 0.3);
  }
  
  .ios-inset-box {
    background: rgba(0, 0, 0, 0.02); /* Чуть светлее вдавленный блок */
    border-radius: 32px;
    box-shadow: 
      inset 0 2px 8px rgba(0, 0, 0, 0.04),
      0 1px 0 rgba(255, 255, 255, 0.6);
  }
  
  .ios-icon-lens {
    background: linear-gradient(135deg, #7000ff 0%, #a855f7 100%);
    border-radius: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 10px 20px rgba(112, 0, 255, 0.2);
  }
  
  .ios-button {
    width: 100%;
    padding: 18px;
    border-radius: 22px;
    font-weight: 800;
    font-size: 16px;
    color: white;
    background: #1a1a2e;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 
      0 15px 30px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .ios-button:hover:not(:disabled) {
    transform: translateY(-2px);
    background: #000;
  }
  
  .ios-button:active {
    transform: scale(0.97);
  }
  
  .ios-button:disabled {
    opacity: 0.5;
  }
  
  .animate-fade-in {
    animation: ios-appear 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  }
  
  @keyframes ios-appear {
    from { 
      opacity: 0; 
      transform: scale(0.9) translateY(20px);
      backdrop-filter: blur(0px);
    }
    to { 
      opacity: 1; 
      transform: scale(1) translateY(0);
      backdrop-filter: blur(30px);
    }
  }
  </style>