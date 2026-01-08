<template>
  <div 
    :class="sidebarMode ? '' : 'deal-card-wrapper w-full flex justify-center my-6 px-4'"
  >
    <div 
      class="deal-card glass rounded-[32px] p-6 border-2 shadow-2xl"
      :class="[
        borderColor, 
        sidebarMode 
          ? 'w-full max-h-[500px] flex flex-col' 
          : 'max-w-md w-full'
      ]"
    >
      
      <div class="flex items-center gap-3 mb-4 shrink-0">
        <div class="w-14 h-14 rounded-full flex items-center justify-center text-white shadow-lg shrink-0" :class="statusIconBg">
          <svg v-if="dealData.status === 'pending'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else-if="dealData.status === 'paid'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <svg v-else-if="dealData.status === 'delivered'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <svg v-else-if="dealData.status === 'completed'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else-if="dealData.status === 'cancelled'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <svg v-else class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-[10px] font-bold uppercase tracking-widest" :class="statusTextColor">
            {{ statusLabel }}
          </div>
          <div class="text-lg font-bold text-[#1a1a2e] truncate">{{ dealData.title }}</div>
        </div>
      </div>

      <div 
        :class="sidebarMode 
          ? 'flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin min-h-0' 
          : 'space-y-4'"
      >

        <div class="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-4 border border-purple-200 shrink-0">
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

        <div v-if="dealData.revision_count > 0" class="shrink-0">
          <div class="bg-orange-50 border border-orange-200 rounded-xl p-3 text-sm">
            <span class="font-bold text-orange-800">Доработки: {{ dealData.revision_count }}/{{ dealData.max_revisions }}</span>
          </div>
        </div>

        <div v-if="dealData.status === 'delivered' && dealData.delivery_message" class="shrink-0">
          <div class="bg-green-50 border border-green-200 rounded-xl p-4">
            <div class="text-xs font-bold text-green-800 uppercase tracking-wider mb-2">Результат работы</div>
            <div class="text-sm text-green-900 whitespace-pre-line leading-relaxed">{{ dealData.delivery_message }}</div>
          </div>
        </div>

        <div v-if="dealData.status === 'completed' && dealData.delivery_message" class="shrink-0">
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2">Работа завершена</div>
            <div class="text-sm text-blue-900 whitespace-pre-line leading-relaxed">{{ dealData.delivery_message }}</div>
          </div>
        </div>

        <div class="space-y-2 pb-2" :class="sidebarMode ? '' : 'mt-auto'">

          <button 
            v-if="showUpdatePriceButton"
            @click="showPriceModal = true"
            class="w-full border-2 border-blue-300 text-blue-600 py-2 rounded-xl font-bold hover:bg-blue-50 transition-all"
          >
            Изменить цену
          </button>

          <button 
            v-if="showPayButton"
            @click="payDeal"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading">Обработка...</span>
            <span v-else>Оплатить заказ ({{ dealData.total }}₽)</span>
          </button>

          <button 
            v-if="showDeliverButton"
            @click="showDeliveryModal = true"
            class="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
          >
            Сдать работу
          </button>

          <button 
            v-if="showCompleteButton"
            @click="showCompletionModal = true"
            class="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
          >
            Принять работу и завершить
          </button>

          <button 
            v-if="showRevisionButton"
            @click="showRevisionModal = true"
            class="w-full border-2 border-orange-300 text-orange-600 py-2 rounded-xl font-bold hover:bg-orange-50 transition-all"
          >
            Запросить доработку ({{ dealData.revision_count }}/{{ dealData.max_revisions }})
          </button>

          <button 
            v-if="showCancelButton"
            @click="showCancelModal = true"
            class="w-full border-2 border-red-300 text-red-600 py-2 rounded-xl font-bold hover:bg-red-50 transition-all"
          >
            Отменить заказ
          </button>
        </div>

      </div>
      </div>

    <teleport to="body">
      <div v-if="showPriceModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Изменить цену</h3>
          <p class="text-sm text-gray-600 mb-4">
            Клиент получит уведомление о новой цене. Цену можно изменить только до оплаты.
          </p>
          
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2">Новая цена (₽)</label>
            <input 
              v-model="newPrice" 
              type="number" 
              min="1"
              class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Введите новую цену..."
            >
          </div>
          
          <div class="flex gap-3">
            <button @click="showPriceModal = false; newPrice = dealData.price" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="updatePrice" :disabled="loading || !newPrice || newPrice <= 0" class="flex-1 bg-blue-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Изменить</button>
          </div>
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="showDeliveryModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Сдать работу</h3>
          <textarea 
            v-model="deliveryMessage" 
            rows="4"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4 text-sm"
            placeholder="Опишите что сделано, добавьте ссылки на результат..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showDeliveryModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="deliverWork" :disabled="!deliveryMessage.trim() || loading" class="flex-1 bg-blue-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Сдать</button>
          </div>
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="showCompletionModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl text-center">
          <h3 class="text-xl font-bold mb-4">Принять работу?</h3>
          <p class="text-sm text-gray-600 mb-6">После принятия деньги будут переведены исполнителю.</p>
          
          <div class="mb-6">
            <label class="block text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Оценка работы</label>
            <div class="flex gap-3 justify-center">
              <button 
                v-for="star in 5" 
                :key="star"
                @click="rating = star"
                class="transition-transform hover:scale-125 focus:outline-none"
              >
                <svg 
                   class="w-8 h-8" 
                   :class="star <= rating ? 'text-yellow-400' : 'text-gray-200'"
                   viewBox="0 0 24 24" 
                   fill="currentColor"
                >
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </button>
            </div>
          </div>
          
          <textarea 
            v-model="completionMessage" 
            rows="3"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-green-500 mb-4 text-sm"
            placeholder="Ваш отзыв..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showCompletionModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="completeDeal" :disabled="loading || rating === 0" class="flex-1 bg-green-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Принять</button>
          </div>
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="showRevisionModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Запросить доработку</h3>
          <p class="text-sm text-gray-600 mb-4">Осталось бесплатных доработок: {{ dealData.max_revisions - dealData.revision_count }}</p>
          <textarea 
            v-model="revisionReason" 
            rows="4"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-orange-500 mb-4 text-sm"
            placeholder="Опишите что нужно доработать..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showRevisionModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="requestRevision" :disabled="!revisionReason.trim() || loading" class="flex-1 bg-orange-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Запросить</button>
          </div>
        </div>
      </div>
    </teleport>

    <teleport to="body">
      <div v-if="showCancelModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl text-center">
          <h3 class="text-xl font-bold mb-2 text-red-600">Отменить заказ?</h3>
          <p class="text-sm text-gray-600 mb-4" v-if="dealData.status === 'paid' || dealData.status === 'delivered'">Средства будут возвращены клиенту.</p>
          <textarea 
            v-model="cancelReason" 
            rows="3"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-red-500 mb-4 text-sm"
            placeholder="Причина отмены..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showCancelModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Назад</button>
            <button @click="cancelDeal" :disabled="loading" class="flex-1 bg-red-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Отменить</button>
          </div>
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
  dealData: Object,
  sidebarMode: Boolean
})

const emit = defineEmits(['deal-action'])

const auth = useAuthStore()
const loading = ref(false)

// Модалки
const showDeliveryModal = ref(false)
const showCompletionModal = ref(false)
const showRevisionModal = ref(false)
const showCancelModal = ref(false)
const showPriceModal = ref(false) 

// Сообщения
const deliveryMessage = ref('')
const completionMessage = ref('')
const revisionReason = ref('')
const cancelReason = ref('')
const rating = ref(0)
const newPrice = ref(props.dealData.price) 

// Проверки роли
const isClient = computed(() => String(auth.user.id) === String(props.dealData.client_id))
const isWorker = computed(() => String(auth.user.id) === String(props.dealData.worker_id))

// Стили статуса
const borderColor = computed(() => {
  const colors = {
    'pending': 'border-purple-300',
    'paid': 'border-blue-300',
    'delivered': 'border-green-300',
    'completed': 'border-orange-300',
    'cancelled': 'border-gray-300',
  }
  return colors[props.dealData.status] || 'border-gray-200'
})

const statusIconBg = computed(() => {
  const bgs = {
    'pending': 'bg-gradient-to-br from-purple-400 to-purple-600',
    'paid': 'bg-gradient-to-br from-blue-400 to-blue-600',
    'delivered': 'bg-gradient-to-br from-green-400 to-green-600',
    'completed': 'bg-gradient-to-br from-orange-400 to-orange-600',
    'cancelled': 'bg-gradient-to-br from-gray-400 to-gray-600',
  }
  return bgs[props.dealData.status] || 'bg-gray-500'
})

// ✅ СТАТУС-ИКОНКИ (логика для шаблона)
// statusIcon в скрипте теперь не нужен, так как SVG прописаны прямо в template для большей гибкости стилизации

const statusLabel = computed(() => {
  const labels = {
    'pending': 'Ожидает оплаты',
    'paid': 'В работе',
    'delivered': 'На проверке',
    'completed': 'Завершен',
    'cancelled': 'Отменен',
  }
  return labels[props.dealData.status] || props.dealData.status
})

const statusTextColor = computed(() => {
  const colors = {
    'pending': 'text-purple-600',
    'paid': 'text-blue-600',
    'delivered': 'text-green-600',
    'completed': 'text-orange-600',
    'cancelled': 'text-gray-600',
  }
  return colors[props.dealData.status] || 'text-gray-600'
})

// Показываем кнопки
const showPayButton = computed(() => {
  return isClient.value && props.dealData.can_pay
})

const showDeliverButton = computed(() => {
  return isWorker.value && props.dealData.can_deliver
})

const showCompleteButton = computed(() => {
  return isClient.value && props.dealData.can_complete
})

const showRevisionButton = computed(() => {
  return isClient.value && props.dealData.can_request_revision
})

const showCancelButton = computed(() => {
  return props.dealData.can_cancel
})

const showUpdatePriceButton = computed(() => {
  return isWorker.value && props.dealData.can_update_price
})

// ДЕЙСТВИЯ
const updatePrice = async () => {
  loading.value = true
  try {
    await axios.patch(`/api/market/deals/${props.dealData.deal_id}/update-price/`, {
      price: newPrice.value
    })
    showPriceModal.value = false
    emit('deal-action')
  } catch (e) {
    alert('Ошибка изменения цены: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const payDeal = async () => {
  if (!confirm(`Оплатить заказ на сумму ${props.dealData.total}₽?`)) return
  
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/pay/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка оплаты: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const deliverWork = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/deliver/`, {
      delivery_message: deliveryMessage.value
    })
    showDeliveryModal.value = false
    deliveryMessage.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const completeDeal = async () => {
  if (rating.value === 0) {
    alert('Пожалуйста, поставьте оценку')
    return
  }
  
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/complete/`, {
      rating: rating.value,
      comment: completionMessage.value || 'Спасибо!'
    })
    showCompletionModal.value = false
    completionMessage.value = ''
    rating.value = 0
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const requestRevision = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/revision/`, {
      revision_reason: revisionReason.value
    })
    showRevisionModal.value = false
    revisionReason.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const cancelDeal = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${props.dealData.deal_id}/cancel/`, {
      reason: cancelReason.value || 'Не указана'
    })
    showCancelModal.value = false
    cancelReason.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(112, 0, 255, 0.3);
  border-radius: 10px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgba(112, 0, 255, 0.5);
}
</style>