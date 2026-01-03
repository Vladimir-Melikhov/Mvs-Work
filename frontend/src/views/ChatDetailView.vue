<template>
  <div class="h-[calc(100vh-150px)] flex flex-col max-w-5xl mx-auto pt-4 pb-2 px-4">
    
    <!-- Шапка чата -->
    <div class="glass px-6 py-3 rounded-[24px] flex items-center gap-4 mb-3 border border-white/60 shadow-sm shrink-0">
      <button 
        @click="$router.push('/chats')" 
        class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold"
      >
        ←
      </button>
      
      <div class="w-11 h-11 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-xs font-bold shadow-md overflow-hidden ring-2 ring-white/50">
        <img v-if="partner?.avatar" :src="partner.avatar" class="w-full h-full object-cover">
        <span v-else>{{ getInitials(partner?.name || 'U') }}</span>
      </div>
      
      <div class="flex-1">
        <h2 class="text-lg font-bold text-[#1a1a2e]">
          {{ partner ? partner.name : 'Загрузка...' }}
        </h2>
      </div>

      <!-- Кнопка управления сделкой -->
      <button 
        @click="showDealModal = true"
        class="px-4 py-2 rounded-full font-bold text-sm transition-all shadow-md flex items-center gap-2"
        :class="dealButtonClass"
      >
        <span>{{ dealButtonIcon }}</span>
        <span>{{ dealButtonText }}</span>
      </button>
    </div>

    <!-- Сообщения -->
    <div 
      ref="messagesContainer"
      class="flex-1 glass rounded-[32px] p-6 overflow-y-auto space-y-4 mb-3 border border-white/40 scroll-smooth"
    >
      <div v-if="loading" class="text-center py-10 opacity-50 flex justify-center">
        <div class="w-6 h-6 border-2 border-[#7000ff] border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="messages.length === 0" class="text-center py-20 text-gray-400">
        <div class="text-5xl mb-3 opacity-30">👋</div>
        <p class="text-sm font-medium">Начните диалог или предложите сделку</p>
      </div>

      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        class="animate-scale-in"
      >
        <!-- ИНТЕРАКТИВНАЯ КАРТОЧКА СДЕЛКИ -->
        <DealMessage 
          v-if="msg.message_type !== 'text'"
          :message="msg"
          :deal-data="msg.deal_data"
          @deal-action="refreshMessages"
        />

        <!-- ОБЫЧНОЕ СООБЩЕНИЕ -->
        <div 
          v-else
          class="flex flex-col"
          :class="isMyMessage(msg) ? 'items-end' : 'items-start'"
        >
          <div 
            class="max-w-[85%] md:max-w-[70%] px-5 py-3 text-[15px] leading-relaxed shadow-sm"
            :class="isMyMessage(msg) 
              ? 'bg-[#1a1a2e] text-white rounded-[22px] rounded-br-none' 
              : 'bg-white text-[#1a1a2e] rounded-[22px] rounded-bl-none border border-white/60'"
          >
            <div class="whitespace-pre-wrap">{{ msg.text }}</div>
            
            <div 
              class="text-[10px] mt-1.5 font-medium opacity-60 text-right"
              :class="isMyMessage(msg) ? 'text-white/60' : 'text-gray-400'"
            >
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Ввод сообщения -->
    <div class="glass p-2 rounded-[26px] flex items-center gap-2 border border-white/60 shadow-xl bg-white/40 backdrop-blur-xl shrink-0">
      <input 
        v-model="newMessage" 
        @keydown.enter="sendMessage"
        type="text" 
        placeholder="Напишите сообщение..." 
        class="flex-1 bg-transparent border-none outline-none px-6 py-3.5 text-[#1a1a2e] placeholder-gray-500 font-medium text-[15px]"
      >
      <button 
        @click="sendMessage"
        :disabled="!newMessage.trim() || !isConnected"
        class="w-12 h-12 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] hover:scale-105 transition-all disabled:opacity-50"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
        </svg>
      </button>
    </div>

    <!-- МОДАЛКА: Управление сделкой -->
    <teleport to="body">
      <div v-if="showDealModal" class="fixed inset-0 bg-black/30 z-[200] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl max-h-[90vh] overflow-y-auto">
          
          <!-- Заголовок -->
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-2xl font-bold text-[#1a1a2e]">
              {{ currentDeal ? 'Редактировать сделку' : 'Новая сделка' }}
            </h3>
            <button @click="showDealModal = false" class="text-3xl text-gray-400 hover:text-gray-600">×</button>
          </div>

          <!-- Форма -->
          <div class="space-y-4 mb-6">
            <div>
              <label class="block text-sm font-bold mb-2 text-gray-700">Название</label>
              <input 
                v-model="dealForm.title" 
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/30"
                placeholder="Например: Разработка лендинга"
              >
            </div>
            
            <div>
              <label class="block text-sm font-bold mb-2 text-gray-700">Цена (₽)</label>
              <input 
                v-model="dealForm.price" 
                type="number"
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/30"
                placeholder="5000"
              >
            </div>
            
            <div>
              <label class="block text-sm font-bold mb-2 text-gray-700">Техническое задание</label>
              <textarea 
                v-model="dealForm.description" 
                rows="6"
                class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-[#7000ff]/30"
                placeholder="Подробно опишите что нужно сделать..."
              ></textarea>
            </div>

            <!-- Расчет -->
            <div v-if="dealForm.price" class="bg-purple-50 rounded-xl p-4 border border-purple-200">
              <div class="text-sm space-y-1">
                <div class="flex justify-between">
                  <span>Стоимость работы:</span>
                  <span class="font-bold">{{ dealForm.price }}₽</span>
                </div>
                <div class="flex justify-between">
                  <span>Комиссия (8%):</span>
                  <span class="font-bold">{{ (parseFloat(dealForm.price) * 0.08).toFixed(2) }}₽</span>
                </div>
                <div class="flex justify-between pt-2 border-t border-purple-300">
                  <span class="font-bold">Итого:</span>
                  <span class="font-bold text-lg text-purple-600">{{ (parseFloat(dealForm.price) * 1.08).toFixed(2) }}₽</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Кнопки -->
          <div class="flex gap-3">
            <button 
              @click="showDealModal = false"
              class="flex-1 border-2 border-gray-200 py-3 rounded-xl font-bold text-gray-700 hover:bg-gray-50 transition-all"
            >
              Отмена
            </button>
            <button 
              @click="proposeDeal"
              :disabled="!dealForm.title || !dealForm.price || !dealForm.description || proposing"
              class="flex-1 bg-gradient-to-r from-[#7000ff] to-[#5500cc] text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
            >
              <span v-if="proposing">⏳ Отправка...</span>
              <span v-else>{{ currentDeal ? '✏️ Изменить' : '🤝 Предложить' }}</span>
            </button>
          </div>

          <!-- Кнопка отмены активной сделки -->
          <button 
            v-if="currentDeal && currentDeal.status === 'active'"
            @click="confirmCancelDeal"
            class="w-full mt-3 border-2 border-red-300 text-red-600 py-2 rounded-xl font-bold hover:bg-red-50 transition-all"
          >
            ❌ Отменить сделку
          </button>

        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import axios from 'axios'
import DealMessage from '../components/DealMessage.vue'

const route = useRoute()
const auth = useAuthStore()
const messagesContainer = ref(null)

const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const isConnected = ref(false)
const partner = ref(null)
const currentDeal = ref(null)
const showDealModal = ref(false)
const proposing = ref(false)
let socket = null

const roomId = route.params.id

const dealForm = ref({
  title: '',
  description: '',
  price: ''
})

const isMyMessage = (msg) => String(msg.sender_id) === String(auth.user.id)
const formatTime = (isoString) => new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
const getInitials = (name) => name ? name.substring(0, 1).toUpperCase() : 'U'

const dealButtonClass = computed(() => {
  if (!currentDeal.value) return 'bg-green-500 hover:bg-green-600 text-white'
  if (currentDeal.value.status === 'active') return 'bg-blue-500 hover:bg-blue-600 text-white'
  if (currentDeal.value.status === 'proposed') return 'bg-purple-500 hover:bg-purple-600 text-white'
  if (currentDeal.value.status === 'completed') return 'bg-gray-300 text-gray-600 cursor-not-allowed'
  return 'bg-gray-500 hover:bg-gray-600 text-white'
})

const dealButtonIcon = computed(() => {
  if (!currentDeal.value) return '🤝'
  if (currentDeal.value.status === 'active') return '🎯'
  if (currentDeal.value.status === 'proposed') return '⏳'
  if (currentDeal.value.status === 'completed') return '🎉'
  return '📝'
})

const dealButtonText = computed(() => {
  if (!currentDeal.value) return 'Начать сделку'
  if (currentDeal.value.status === 'active') return 'Завершить'
  if (currentDeal.value.status === 'proposed') return 'Изменить'
  if (currentDeal.value.status === 'completed') return 'Завершена'
  return 'Сделка'
})

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const fetchRoomDetails = async () => {
  try {
    const res = await axios.get(`/api/chat/rooms/${roomId}/`)
    if (res.data.status === 'success') {
      const members = res.data.data.members
      const partnerId = members.find(id => String(id) !== String(auth.user.id))
      
      if (partnerId) {
        const userRes = await axios.post('/api/auth/users/batch/', { user_ids: [partnerId] })
        if (userRes.data.status === 'success' && userRes.data.data.length > 0) {
          partner.value = userRes.data.data[0]
        }
      }
    }
  } catch (e) {
    console.error("Room info error:", e)
  }
}

const fetchDeal = async () => {
  try {
    const res = await axios.get(`/api/market/deals/by-chat/${roomId}/`)
    if (res.data.status === 'success' && res.data.data) {
      currentDeal.value = res.data.data
      
      // Предзаполняем форму если есть активная сделка
      if (currentDeal.value) {
        dealForm.value = {
          title: currentDeal.value.title,
          description: currentDeal.value.description,
          price: currentDeal.value.price
        }
      }
    }
  } catch (e) {
    console.error("Deal fetch error:", e)
  }
}

const fetchHistory = async () => {
  try {
    const res = await axios.get(`/api/chat/rooms/${roomId}/messages/`)
    if (res.data.status === 'success') {
      messages.value = res.data.data
      scrollToBottom()
    }
  } catch (e) {
    console.error("History error:", e)
  } finally {
    loading.value = false
  }
}

const refreshMessages = async () => {
  await fetchHistory()
  await fetchDeal()
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}/`
  
  socket = new WebSocket(wsUrl)

  socket.onopen = () => { isConnected.value = true }
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    // ✅ Обработка обновления существующего сообщения
    if (data.type === 'message_updated') {
      const updatedMsg = data.data
      const index = messages.value.findIndex(m => String(m.id) === String(updatedMsg.id))
      if (index !== -1) {
        // Обновляем существующее сообщение
        messages.value[index] = { ...messages.value[index], ...updatedMsg }
      }
    }
    // Обработка нового сообщения
    else if (data.type === 'message') {
      messages.value.push(data.data)
      scrollToBottom()
    }
  }

  socket.onclose = () => { isConnected.value = false }
}

const sendMessage = () => {
  if (!newMessage.value.trim() || !isConnected.value) return

  const payload = {
    type: 'message',
    sender_id: auth.user.id,
    text: newMessage.value
  }

  socket.send(JSON.stringify(payload))
  newMessage.value = ''
}

const proposeDeal = async () => {
  proposing.value = true
  try {
    await axios.post('/api/market/deals/propose/', {
      chat_room_id: roomId,
      title: dealForm.value.title,
      description: dealForm.value.description,
      price: dealForm.value.price
    })
    
    showDealModal.value = false
    await refreshMessages()
    
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    proposing.value = false
  }
}

const confirmCancelDeal = async () => {
  if (!confirm('Отменить сделку? Средства будут возвращены клиенту.')) return
  
  try {
    await axios.post(`/api/market/deals/${currentDeal.value.id}/cancel/`, {
      reason: 'Отменено по взаимному согласию'
    })
    
    showDealModal.value = false
    await refreshMessages()
    
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  }
}

onMounted(() => {
  fetchRoomDetails()
  fetchDeal()
  fetchHistory()
  connectWebSocket()
})

onUnmounted(() => {
  if (socket) socket.close()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(30px);
  box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.05);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.98) translateY(5px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.animate-scale-in {
  animation: scale-in 0.15s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}
</style>
