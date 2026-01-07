<template>
  <!-- Desktop: двухколоночный layout -->
  <div class="hidden md:flex h-[calc(100vh-150px)] gap-4 max-w-7xl mx-auto pt-4 pb-2 px-4">
    
    <!-- Левая часть: Чат -->
    <div class="flex-1 flex flex-col min-w-0">
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
      </div>

      <div 
        ref="messagesContainer"
        class="flex-1 glass rounded-[32px] p-6 overflow-y-auto space-y-4 mb-3 border border-white/40 scroll-smooth"
      >
        <div v-if="loading" class="text-center py-10 opacity-50 flex justify-center">
          <div class="w-6 h-6 border-2 border-[#7000ff] border-t-transparent rounded-full animate-spin"></div>
        </div>

        <div v-else-if="textMessages.length === 0" class="text-center py-20 text-gray-400">
          <div class="text-5xl mb-3 opacity-30">👋</div>
          <p class="text-sm font-medium">Начните диалог</p>
        </div>

        <div 
          v-for="msg in textMessages" 
          :key="msg.id" 
          class="animate-scale-in flex flex-col"
          :class="isMyMessage(msg) ? 'items-end' : 'items-start'"
        >
          <div 
            class="max-w-[75%] px-5 py-3 text-[15px] leading-relaxed shadow-sm"
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
    </div>

    <div class="w-96 shrink-0 flex flex-col">
      <div v-if="activeDeals.length === 0" class="glass rounded-[32px] p-6 border border-white/40 flex flex-col items-center justify-center text-center h-full">
        <div class="text-5xl mb-3 opacity-30">📋</div>
        <p class="text-sm text-gray-500 mb-4">Заказов пока нет</p>
      </div>

      <div v-else class="flex flex-col gap-3 overflow-y-auto">
        <div 
          v-for="(deal, index) in activeDeals" 
          :key="deal.deal_id"
          class="glass rounded-[24px] border border-white/40 overflow-hidden"
        >
          <div 
            @click="toggleDeal(index)"
            class="p-4 cursor-pointer hover:bg-white/20 transition-all flex items-center justify-between"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-bold text-[#1a1a2e] truncate">{{ deal.title }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ getStatusLabel(deal.status) }}</div>
            </div>
            <div class="flex items-center gap-2">
              <div class="text-[#7000ff] font-bold text-sm">{{ deal.price }}₽</div>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-5 w-5 text-gray-400 transition-transform"
                :class="expandedDealIndex === index ? 'rotate-180' : ''"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div 
            v-if="expandedDealIndex === index"
            class="border-t border-white/20"
          >
            <DealMessage 
              :message="dealMessages.find(m => m.deal_data?.deal_id === deal.deal_id)"
              :deal-data="deal"
              @deal-action="refreshMessages"
              sidebar-mode
            />
          </div>
        </div>
      </div>
    </div>

  </div>

  <div class="md:hidden h-[calc(100vh-150px)] flex flex-col px-4 pt-4 pb-2">
    
    <div class="glass px-4 py-3 rounded-[24px] flex items-center gap-3 mb-3 border border-white/60 shadow-sm shrink-0">
      <button 
        @click="$router.push('/chats')" 
        class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold"
      >
        ←
      </button>
      
      <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-xs font-bold shadow-md overflow-hidden ring-2 ring-white/50">
        <img v-if="partner?.avatar" :src="partner.avatar" class="w-full h-full object-cover">
        <span v-else>{{ getInitials(partner?.name || 'U') }}</span>
      </div>
      
      <div class="flex-1 min-w-0">
        <h2 class="text-base font-bold text-[#1a1a2e] truncate">
          {{ partner ? partner.name : 'Загрузка...' }}
        </h2>
      </div>

      <button 
        v-if="activeDeals.length > 0"
        @click="mobileShowDeal = !mobileShowDeal"
        class="w-9 h-9 flex items-center justify-center rounded-full transition-all font-bold relative"
        :class="mobileShowDeal ? 'bg-[#7000ff] text-white' : 'bg-white/40 text-[#1a1a2e]'"
      >
        📋
        <span v-if="activeDeals.length > 1" class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {{ activeDeals.length }}
        </span>
      </button>
    </div>

    <div v-if="!mobileShowDeal" class="flex-1 flex flex-col min-h-0">
      <div 
        ref="messagesContainer"
        class="flex-1 glass rounded-[32px] p-4 overflow-y-auto space-y-3 mb-3 border border-white/40 scroll-smooth"
      >
        <div v-if="loading" class="text-center py-10 opacity-50 flex justify-center">
          <div class="w-6 h-6 border-2 border-[#7000ff] border-t-transparent rounded-full animate-spin"></div>
        </div>

        <div v-else-if="textMessages.length === 0" class="text-center py-20 text-gray-400">
          <div class="text-5xl mb-3 opacity-30">👋</div>
          <p class="text-sm font-medium">Начните диалог</p>
        </div>

        <div 
          v-for="msg in textMessages" 
          :key="msg.id" 
          class="animate-scale-in flex flex-col"
          :class="isMyMessage(msg) ? 'items-end' : 'items-start'"
        >
          <div 
            class="max-w-[85%] px-4 py-2.5 text-sm leading-relaxed shadow-sm"
            :class="isMyMessage(msg) 
              ? 'bg-[#1a1a2e] text-white rounded-[18px] rounded-br-none' 
              : 'bg-white text-[#1a1a2e] rounded-[18px] rounded-bl-none border border-white/60'"
          >
            <div class="whitespace-pre-wrap">{{ msg.text }}</div>
            
            <div 
              class="text-[9px] mt-1 font-medium opacity-60 text-right"
              :class="isMyMessage(msg) ? 'text-white/60' : 'text-gray-400'"
            >
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Поле ввода -->
      <div class="glass p-2 rounded-[26px] flex items-center gap-2 border border-white/60 shadow-xl bg-white/40 backdrop-blur-xl shrink-0">
        <input 
          v-model="newMessage" 
          @keydown.enter="sendMessage"
          type="text" 
          placeholder="Сообщение..." 
          class="flex-1 bg-transparent border-none outline-none px-4 py-3 text-[#1a1a2e] placeholder-gray-500 font-medium text-sm"
        >
        <button 
          @click="sendMessage"
          :disabled="!newMessage.trim() || !isConnected"
          class="w-11 h-11 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] transition-all disabled:opacity-50"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile: Список заказов -->
    <div v-else class="flex-1 overflow-y-auto space-y-3">
      <div v-if="activeDeals.length === 0" class="glass rounded-[32px] p-6 border border-white/40 flex flex-col items-center justify-center text-center h-full">
        <div class="text-5xl mb-3 opacity-30">📋</div>
        <p class="text-sm text-gray-500 mb-4">Заказов пока нет</p>
      </div>

      <div v-else>
        <div 
          v-for="(deal, index) in activeDeals" 
          :key="deal.deal_id"
          class="glass rounded-[24px] border border-white/40 overflow-hidden mb-3"
        >
          <div 
            @click="toggleDeal(index)"
            class="p-4 cursor-pointer hover:bg-white/20 transition-all flex items-center justify-between"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-bold text-[#1a1a2e] truncate">{{ deal.title }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ getStatusLabel(deal.status) }}</div>
            </div>
            <div class="flex items-center gap-2">
              <div class="text-[#7000ff] font-bold text-sm">{{ deal.price }}₽</div>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-5 w-5 text-gray-400 transition-transform"
                :class="expandedDealIndex === index ? 'rotate-180' : ''"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div 
            v-if="expandedDealIndex === index"
            class="border-t border-white/20"
          >
            <DealMessage 
              :message="dealMessages.find(m => m.deal_data?.deal_id === deal.deal_id)"
              :deal-data="deal"
              @deal-action="refreshMessages"
              sidebar-mode
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
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
const mobileShowDeal = ref(false)
const expandedDealIndex = ref(0)
let socket = null
const roomId = route.params.id

// Вычисляем только ТЕКСТОВЫЕ сообщения
const textMessages = computed(() => {
  return messages.value.filter(m => m.message_type === 'text')
})

// Все deal-сообщения
const dealMessages = computed(() => {
  return messages.value.filter(m => m.message_type !== 'text')
})

// Все активные заказы
const activeDeals = computed(() => {
  return dealMessages.value
    .map(m => m.deal_data)
    .filter(d => d && d.deal_id)
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
})

const isMyMessage = (msg) => String(msg.sender_id) === String(auth.user.id)
const formatTime = (isoString) => new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
const getInitials = (name) => name ? name.substring(0, 1).toUpperCase() : 'U'

const getStatusLabel = (status) => {
  const labels = {
    'pending': 'Ожидает оплаты',
    'paid': 'В работе',
    'delivered': 'Сдано',
    'completed': 'Завершено',
    'cancelled': 'Отменено',
  }
  return labels[status] || status
}

const toggleDeal = (index) => {
  expandedDealIndex.value = expandedDealIndex.value === index ? null : index
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

const fetchRoomDetails = async () => {
  try {
    const res = await axios.get(`/api/chat/rooms/${roomId}/`)
    const partnerId = res.data.data.members.find(id => String(id) !== String(auth.user.id))
    if (partnerId) {
      const userRes = await axios.post('/api/auth/users/batch/', { user_ids: [partnerId] })
      partner.value = userRes.data.data[0]
    }
  } catch (e) { console.error(e) }
}

const fetchHistory = async () => {
  try {
    const res = await axios.get(`/api/chat/rooms/${roomId}/messages/`)
    messages.value = res.data.data
    scrollToBottom()
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const refreshMessages = () => fetchHistory()

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/${roomId}/`)
  socket.onopen = () => isConnected.value = true
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'message') {
      messages.value.push(data.data)
      scrollToBottom()
    } else if (data.type === 'message_updated') {
      const idx = messages.value.findIndex(m => String(m.id) === String(data.data.id))
      if (idx !== -1) messages.value[idx] = data.data
    }
  }
  socket.onclose = () => isConnected.value = false
}

const sendMessage = () => {
  if (!newMessage.value.trim() || !isConnected.value) return
  socket.send(JSON.stringify({ type: 'message', sender_id: auth.user.id, text: newMessage.value }))
  newMessage.value = ''
}

onMounted(() => {
  fetchRoomDetails()
  fetchHistory()
  connectWebSocket()
})
onUnmounted(() => { if (socket) socket.close() })
</script>

<style scoped>
.glass { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(30px); }
@keyframes scale-in { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
.animate-scale-in { animation: scale-in 0.15s ease forwards; }
</style>
