<template>
  <div class="deal-message-wrapper w-full flex justify-center my-6 px-4">
    <div class="deal-card glass rounded-[32px] p-6 max-w-md w-full border-2 shadow-2xl" :class="borderColor">
      
      <!-- PROPOSED - Предложение сделки -->
      <div v-if="dealData.status === 'proposed'">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center text-white text-2xl shadow-lg">
            🤝
          </div>
          <div>
            <div class="text-xs text-purple-600 font-bold uppercase tracking-wider">Предложение сделки</div>
            <div class="text-lg font-bold text-[#1a1a2e]">{{ dealData.title }}</div>
          </div>
        </div>

        <div class="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-4 mb-4 border border-purple-200">
          <div class="text-sm text-gray-700 whitespace-pre-line mb-3 max-h-32 overflow-y-auto custom-scrollbar">
            {{ dealData.description }}
          </div>
          
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600">Стоимость работы:</span>
              <span class="font-bold">{{ dealData.price }}₽</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Комиссия сервиса (8%):</span>
              <span class="font-bold">{{ dealData.commission }}₽</span>
            </div>
            <div class="flex justify-between pt-2 border-t border-purple-200">
              <span class="font-bold">Итого к оплате:</span>
              <span class="font-bold text-lg text-purple-600">{{ dealData.total }}₽</span>
            </div>
          </div>
        </div>

        <!-- Статус подтверждений -->
        <div class="flex items-center gap-3 mb-4 text-sm">
          <div class="flex items-center gap-1">
            <span v-if="dealData.client_confirmed" class="text-green-500 font-bold">✅</span>
            <span v-else class="text-gray-300 font-bold">⏳</span>
            <span class="text-gray-600">Клиент</span>
          </div>
          <div class="h-4 w-px bg-gray-300"></div>
          <div class="flex items-center gap-1">
            <span v-if="dealData.worker_confirmed" class="text-green-500 font-bold">✅</span>
            <span v-else class="text-gray-300 font-bold">⏳</span>
            <span class="text-gray-600">Исполнитель</span>
          </div>
        </div>

        <!-- Действия -->
        <div v-if="!isMyProposal && !isConfirmedByMe" class="space-y-2">
          <button 
            @click="confirmDeal"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading">⏳ Подтверждаю...</span>
            <span v-else>✅ Принять условия</span>
          </button>
          <button 
            @click="showRejectModal = true"
            class="w-full border-2 border-red-300 text-red-600 py-2 rounded-xl font-bold hover:bg-red-50 transition-all"
          >
            ❌ Отклонить
          </button>
        </div>

        <div v-else-if="isMyProposal" class="bg-blue-50 rounded-xl p-3 text-sm text-blue-800 text-center">
          ⏳ Ожидаем подтверждения второй стороны...
        </div>

        <div v-else class="bg-green-50 rounded-xl p-3 text-sm text-green-800 text-center">
          ✅ Вы подтвердили. Ожидаем второй стороны...
        </div>
      </div>

      <!-- ACTIVE - Сделка активна -->
      <div v-else-if="dealData.status === 'active'">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center text-white text-2xl shadow-lg">
            ✅
          </div>
          <div>
            <div class="text-xs text-green-600 font-bold uppercase tracking-wider">Сделка активирована</div>
            <div class="text-lg font-bold text-[#1a1a2e]">{{ dealData.title }}</div>
          </div>
        </div>

        <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-4 mb-4 border border-green-200">
          <div class="flex items-start gap-3 mb-3">
            <span class="text-2xl">💰</span>
            <div class="text-sm">
              <div class="font-bold text-green-800 mb-1">Средства захолдированы</div>
              <div class="text-green-700">{{ dealData.price }}₽ надежно удерживаются до завершения работы</div>
            </div>
          </div>
          <div class="text-xs text-green-600">
            Активирована: {{ formatDateTime(dealData.activated_at) }}
          </div>
        </div>

        <div class="bg-blue-50 rounded-xl p-3 text-sm text-blue-800 mb-4">
          <div class="font-bold mb-1">📋 Что дальше?</div>
          <div>Исполнитель выполняет работу. После завершения любая сторона может запросить завершение сделки.</div>
        </div>
      </div>

      <!-- COMPLETION_REQUESTED - Запрос завершения -->
      <div v-else-if="dealData.status === 'completion_requested'">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-2xl shadow-lg">
            🎯
          </div>
          <div>
            <div class="text-xs text-blue-600 font-bold uppercase tracking-wider">Запрос на завершение</div>
            <div class="text-lg font-bold text-[#1a1a2e]">{{ dealData.title }}</div>
          </div>
        </div>

        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-4 mb-4 border border-blue-200">
          <div class="text-sm text-blue-900 mb-2">
            <span class="font-bold">{{ dealData.requester_role === 'client' ? 'Клиент' : 'Исполнитель' }}</span> 
            запросил завершение сделки на сумму 
            <span class="font-bold">{{ dealData.price }}₽</span>
          </div>
        </div>

        <!-- Кнопки для второй стороны -->
        <div v-if="!isRequester" class="space-y-2">
          <button 
            @click="completeDeal"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading">⏳ Завершаю...</span>
            <span v-else>✅ Подтвердить завершение</span>
          </button>
          <button 
            @click="showDisputeModal = true"
            class="w-full border-2 border-orange-300 text-orange-600 py-2 rounded-xl font-bold hover:bg-orange-50 transition-all"
          >
            ⚠️ Есть замечания
          </button>
        </div>

        <div v-else class="bg-blue-50 rounded-xl p-3 text-sm text-blue-800 text-center">
          ⏳ Ожидаем подтверждения второй стороны...
        </div>
      </div>

      <!-- COMPLETED - Завершена -->
      <div v-else-if="dealData.status === 'completed'">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-white text-2xl shadow-lg animate-bounce-slow">
            🎉
          </div>
          <div>
            <div class="text-xs text-orange-600 font-bold uppercase tracking-wider">Сделка завершена</div>
            <div class="text-lg font-bold text-[#1a1a2e]">{{ dealData.title }}</div>
          </div>
        </div>

        <div class="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-4 border border-orange-200">
          <div class="flex items-start gap-3 mb-2">
            <span class="text-2xl">💸</span>
            <div class="text-sm">
              <div class="font-bold text-orange-800 mb-1">Оплата переведена</div>
              <div class="text-orange-700">{{ dealData.price }}₽ успешно переведено исполнителю</div>
            </div>
          </div>
          <div class="text-xs text-orange-600">
            Завершена: {{ formatDateTime(dealData.completed_at) }}
          </div>
        </div>
      </div>

      <!-- CANCELLED - Отменена -->
      <div v-else-if="dealData.status === 'cancelled'">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-white text-2xl shadow-lg opacity-70">
            ❌
          </div>
          <div>
            <div class="text-xs text-gray-600 font-bold uppercase tracking-wider">Сделка отменена</div>
            <div class="text-lg font-bold text-gray-700">{{ dealData.title }}</div>
          </div>
        </div>

        <div class="bg-gray-100 rounded-2xl p-4 border border-gray-300">
          <div class="text-sm text-gray-700 mb-2">
            <span class="font-bold">{{ dealData.canceller_role === 'client' ? 'Клиент' : 'Исполнитель' }}</span> 
            отменил сделку
          </div>
          <div v-if="dealData.reason" class="text-sm text-gray-600 italic">
            "{{ dealData.reason }}"
          </div>
          <div v-if="dealData.was_active" class="text-xs text-green-600 mt-2 font-bold">
            💸 Средства возвращены клиенту
          </div>
        </div>
      </div>

    </div>

    <!-- Модалка отклонения -->
    <teleport to="body">
      <div v-if="showRejectModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Отклонить предложение?</h3>
          <p class="text-sm text-gray-600 mb-4">Вы можете предложить свои условия или отменить сделку.</p>
          <div class="flex gap-3">
            <button @click="showRejectModal = false" class="flex-1 border-2 py-2 rounded-lg">Назад</button>
            <button @click="rejectDeal" class="flex-1 bg-red-500 text-white py-2 rounded-lg font-bold">Отклонить</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Модалка спора -->
    <teleport to="body">
      <div v-if="showDisputeModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Есть замечания?</h3>
          <p class="text-sm text-gray-600 mb-4">Опишите проблему в чате. Исполнитель должен доработать.</p>
          <button @click="showDisputeModal = false" class="w-full bg-orange-500 text-white py-3 rounded-lg font-bold">Понятно</button>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const props = defineProps({
  message: Object,
  dealData: Object
})

const emit = defineEmits(['deal-action'])

const auth = useAuthStore()
const loading = ref(false)
const showRejectModal = ref(false)
const showDisputeModal = ref(false)

const isMyProposal = computed(() => {
  return String(auth.user.id) === String(props.dealData?.proposer_id)
})

const isConfirmedByMe = computed(() => {
  if (!props.dealData) return false
  const myId = String(auth.user.id)
  const clientId = String(props.dealData.client_id)
  const workerId = String(props.dealData.worker_id)
  
  // Я клиент?
  if (myId === clientId) {
    return props.dealData.client_confirmed
  }
  // Я исполнитель?
  if (myId === workerId) {
    return props.dealData.worker_confirmed
  }
  return false
})

const isRequester = computed(() => {
  return String(auth.user.id) === String(props.dealData?.requester_id)
})

const borderColor = computed(() => {
  const status = props.dealData?.status
  if (status === 'proposed') return 'border-purple-300'
  if (status === 'active') return 'border-green-300'
  if (status === 'completion_requested') return 'border-blue-300'
  if (status === 'completed') return 'border-orange-300'
  if (status === 'cancelled') return 'border-gray-300'
  return 'border-gray-200'
})

const confirmDeal = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/confirm/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const rejectDeal = async () => {
  showRejectModal.value = false
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/cancel/`, {
      reason: 'Не устраивают условия'
    })
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  }
}

const completeDeal = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/complete/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const formatDateTime = (isoString) => {
  if (!isoString) return ''
  return new Date(isoString).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}

@keyframes bounce-slow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.animate-bounce-slow {
  animation: bounce-slow 2s infinite;
}
</style>
