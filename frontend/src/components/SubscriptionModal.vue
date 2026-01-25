// frontend/src/components/SubscriptionModal.vue
<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>
    
    <div class="relative glass p-8 rounded-[32px] max-w-md w-full shadow-2xl border border-white/20 animate-scale-in">
      <button 
        @click="$emit('close')" 
        class="absolute top-4 right-4 text-gray-400 hover:text-[#1a1a2e] transition-colors"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div class="text-center">
        <div class="w-16 h-16 rounded-full bg-gradient-to-br from-[#7000ff] to-[#00c6ff] mx-auto mb-4 flex items-center justify-center">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <h2 class="text-2xl font-bold text-[#1a1a2e] mb-2">Активировать подписку</h2>
        <p class="text-gray-600 mb-6">Получите доступ к публикации объявлений</p>

        <div class="bg-white/30 rounded-2xl p-6 mb-6 border border-white/40">
          <div class="flex items-center justify-center gap-2 mb-2">
            <span class="text-4xl font-bold text-[#1a1a2e]">444</span>
            <span class="text-2xl font-bold text-gray-600">₽</span>
          </div>
          <p class="text-sm text-gray-600">в месяц</p>
        </div>

        <div class="text-left space-y-3 mb-6">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="text-sm text-gray-700">Публикация неограниченного количества объявлений</span>
          </div>
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="text-sm text-gray-700">Приоритетная поддержка</span>
          </div>
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="text-sm text-gray-700">Без комиссии с заказов</span>
          </div>
        </div>

        <button 
          @click="subscribe"
          :disabled="loading"
          class="w-full bg-[#1a1a2e] text-white py-4 rounded-2xl font-bold hover:scale-105 transition-transform shadow-lg shadow-[#1a1a2e]/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Обработка...' : 'Оплатить подписку' }}
        </button>

        <p class="text-xs text-gray-500 mt-4">
          Подписка автоматически продлевается каждый месяц
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['close', 'subscribed'])

const loading = ref(false)

const subscribe = async () => {
  try {
    loading.value = true
    
    const response = await axios.post('http://localhost:8001/api/auth/subscription/')
    
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
@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}

.animate-scale-in {
  animation: scale-in 0.3s ease-out;
}
</style>
