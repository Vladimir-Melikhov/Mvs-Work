<template>
  <div class="h-[calc(100vh-150px)] flex flex-col max-w-5xl mx-auto pt-4 pb-2 px-4">
    
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

      <div v-else-if="messages.length === 0" class="text-center py-20 text-gray-400">
        <div class="text-5xl mb-3 opacity-30">👋</div>
        <p class="text-sm font-medium">Начните диалог или предложите сделку</p>
      </div>

      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        class="animate-scale-in"
      >
        <DealMessage 
          v-if="msg.message_type !== 'text'"
          :message="msg"
          :deal-data="msg.deal_data"
          @deal-action="refreshMessages"
        />

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

    <teleport to="body">
      <div v-if="showDealModal" class="fixed inset-0 bg-black/30 z-[200] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl max-h-[90vh] overflow-y-auto">
          
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-2xl font-bold text-[#1a1a2e]">
              Новая сделка
            </h3>
            <button @click="showDealModal = false" class="text-3xl text-gray-400 hover:text-gray-600">×</button>
          </div>

          <div class="space-y-4 mb-6">
            <div>
              <label class="block text-sm font-bold mb-2 text-gray-700">Название</label>
              <input 
                v-model="dealForm.title" 
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/30"
              >
            </div>
            
            <div>
              <label class="block text-sm font-bold mb-2 text-gray-700">Цена (₽)</label>
              <input 
                v-model="dealForm.price" 
                type="number"
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/30"
              >
            </div>
            
            <div>
              <label class="block text-sm font-bold mb-2 text-gray-700">Техническое задание</label>
              <textarea 
                v-model="dealForm.description" 
                rows="6"
                class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-[#7000ff]/30"
              ></textarea>
            </div>

            <div v-if="dealForm.price" class="bg-purple-50 rounded-xl p-4 border border-purple-200">
              <div class="text-sm space-y-1">
                <div class="flex justify-between">
                  <span>Стоимость: {{ dealForm.price }}₽</span>
                </div>
                <div class="flex justify-between pt-2 border-t border-purple-300">
                  <span class="font-bold">Итого: {{ (parseFloat(dealForm.price) * 1.08).toFixed(2) }}₽</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flex gap-3">
            <button @click="showDealModal = false" class="flex-1 border-2 py-3 rounded-xl font-bold">Отмена</button>
            <button @click="proposeDeal" :disabled="proposing" class="flex-1 bg-[#1a1a2e] text-white py-3 rounded-xl font-bold">Предложить</button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
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
const showDealModal = ref(false)
const proposing = ref(false)
let socket = null
const roomId = route.params.id

const dealForm = ref({ title: '', description: '', price: '' })

const isMyMessage = (msg) => String(msg.sender_id) === String(auth.user.id)
const formatTime = (isoString) => new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
const getInitials = (name) => name ? name.substring(0, 1).toUpperCase() : 'U'

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

const proposeDeal = async () => {
  proposing.value = true
  try {
    await axios.post('/api/market/deals/propose/', { chat_room_id: roomId, ...dealForm.value })
    showDealModal.value = false
    refreshMessages()
  } catch (e) { alert(e.message) } finally { proposing.value = false }
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