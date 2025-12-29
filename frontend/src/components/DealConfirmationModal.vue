<template>
    <div v-if="show" class="fixed inset-0 bg-black/30 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in">
      <div class="bg-white rounded-[32px] p-8 max-w-2xl w-full shadow-2xl relative border border-white/50 max-h-[90vh] overflow-y-auto">
        
        <button 
          @click="$emit('close')" 
          class="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 transition-colors flex items-center justify-center font-bold text-xl"
        >
          ×
        </button>
  
        <div v-if="step === 1">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-2xl">
              🤝
            </div>
            <div>
              <h2 class="text-2xl font-bold text-[#1a1a2e]">Предложить сделку</h2>
              <p class="text-sm text-gray-500">Обе стороны должны подтвердить условия</p>
            </div>
          </div>
  
          <div class="bg-[#7000ff]/5 rounded-2xl p-6 mb-6 border border-[#7000ff]/10">
            <h3 class="font-bold text-[#1a1a2e] mb-3">📋 Техническое задание</h3>
            <div class="prose prose-sm max-w-none text-gray-600 whitespace-pre-line max-h-[300px] overflow-y-auto">
              {{ order.agreed_tz }}
            </div>
          </div>
  
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
            <div class="flex items-start gap-3">
              <div class="text-xl">💰</div>
              <div class="text-sm text-amber-800">
                <div class="font-bold mb-2">Стоимость и комиссия:</div>
                <div class="space-y-1">
                  <div>Цена услуги: <span class="font-bold">{{ order.price }}₽</span></div>
                  <div>Комиссия сервиса (8%): <span class="font-bold">{{ commission }}₽</span></div>
                  <div class="pt-2 border-t border-amber-300">
                    Итого к оплате: <span class="font-bold text-lg">{{ total }}₽</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
  
          <div v-if="order.client_confirmed || order.worker_confirmed" class="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
            <div class="flex items-start gap-3">
              <div class="text-xl">⏳</div>
              <div class="text-sm text-blue-800">
                <div class="font-bold mb-1">Ожидаем подтверждения:</div>
                <div>
                  <span v-if="order.client_confirmed">✅ Клиент подтвердил</span>
                  <span v-else>⏳ Клиент еще не подтвердил</span>
                </div>
                <div>
                  <span v-if="order.worker_confirmed">✅ Исполнитель подтвердил</span>
                  <span v-else>⏳ Исполнитель еще не подтвердил</span>
                </div>
              </div>
            </div>
          </div>
  
          <div class="flex gap-4">
            <button 
              @click="$emit('close')" 
              class="flex-1 border-2 border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-bold text-gray-700"
            >
              Отмена
            </button>
            <button 
              @click="proposeDeal" 
              :disabled="loading"
              class="flex-1 bg-[#7000ff] hover:bg-[#5500cc] text-white py-3 rounded-xl shadow-lg shadow-[#7000ff]/20 hover:shadow-xl hover:scale-[1.01] transition-all font-bold disabled:opacity-50"
            >
              <span v-if="loading">⏳ Отправка...</span>
              <span v-else>✅ Подтвердить условия</span>
            </button>
          </div>
        </div>
  
        <div v-if="step === 2">
          <div class="text-center py-10">
            <div class="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center text-5xl mx-auto mb-6">
              🎉
            </div>
            <h3 class="text-2xl font-bold text-[#1a1a2e] mb-2">Сделка подтверждена!</h3>
            <p class="text-gray-600 mb-8">{{ successMessage }}</p>
            
            <button 
              @click="$emit('close'); $router.push('/chats')" 
              class="bg-[#1a1a2e] text-white px-8 py-3 rounded-xl font-bold"
            >
              Перейти в чаты
            </button>
          </div>
        </div>
  
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  
  const props = defineProps({
    show: Boolean,
    order: Object
  })
  
  const emit = defineEmits(['close', 'updated'])
  
  const step = ref(1)
  const loading = ref(false)
  const successMessage = ref('')
  
  const commission = computed(() => {
    if (!props.order) return 0
    return (props.order.price * 0.08).toFixed(2)
  })
  
  const total = computed(() => {
    if (!props.order) return 0
    return (parseFloat(props.order.price) + parseFloat(commission.value)).toFixed(2)
  })
  
  const proposeDeal = async () => {
    loading.value = true
    
    try {
      const res = await axios.post(`/api/market/orders/${props.order.id}/propose/`)
      
      if (res.data.status === 'success') {
        successMessage.value = res.data.data.message
        step.value = 2
        emit('updated', res.data.data.order)
      } else {
        alert('Ошибка: ' + res.data.error)
      }
    } catch (e) {
      console.error('Propose error:', e)
      alert('Ошибка при подтверждении: ' + (e.response?.data?.error || e.message))
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <style scoped>
  @keyframes fade-in {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }
  
  .animate-fade-in {
    animation: fade-in 0.2s ease-out;
  }
  </style>
