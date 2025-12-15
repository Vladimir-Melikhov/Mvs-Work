<template>
    <div class="h-[calc(100vh-150px)] flex flex-col max-w-5xl mx-auto pt-4 pb-2 px-4 animate-fade-in">
      
      <div class="glass px-6 py-3 rounded-[24px] flex items-center gap-4 mb-3 border border-white/60 shadow-sm relative z-20 shrink-0">
        <button 
          @click="$router.push('/chats')" 
          class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold shadow-sm"
        >
          ←
        </button>
        
        <div class="w-11 h-11 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-xs font-bold shadow-md overflow-hidden ring-2 ring-white/50">
          <img v-if="partner?.avatar" :src="partner.avatar" class="w-full h-full object-cover">
          <span v-else>{{ getInitials(partner?.name || 'C') }}</span>
        </div>
        
        <div>
          <h2 class="text-lg font-bold text-[#1a1a2e] leading-tight tracking-tight">
              {{ partner ? partner.name : 'Загрузка...' }}
          </h2>
          <p class="text-[11px] text-gray-500 font-medium opacity-80 flex items-center gap-1.5">
             <span v-if="isConnected" class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
             {{ isConnected ? 'В сети' : 'Подключение...' }}
          </p>
        </div>
      </div>
  
      <div 
        ref="messagesContainer"
        class="flex-1 glass rounded-[32px] p-6 overflow-y-auto space-y-4 mb-3 border border-white/40 shadow-inner scroll-smooth relative"
      >
        <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
  
        <div v-if="loading" class="text-center py-10 opacity-50 flex justify-center">
          <div class="w-6 h-6 border-2 border-[#7000ff] border-t-transparent rounded-full animate-spin"></div>
        </div>
  
        <div v-else-if="messages.length === 0" class="text-center py-20 text-gray-400">
          <div class="text-5xl mb-3 grayscale opacity-30">👋</div>
          <p class="text-sm font-medium">Начните диалог первым</p>
        </div>
  
        <div 
          v-for="(msg, index) in messages" 
          :key="msg.id" 
          class="flex flex-col animate-scale-in relative z-10"
          :class="isMyMessage(msg) ? 'items-end' : 'items-start'"
        >
          <div 
            class="max-w-[85%] md:max-w-[75%] px-5 py-3 text-[15px] leading-relaxed shadow-sm relative group transition-all hover:shadow-md"
            :class="isMyMessage(msg) 
              ? 'bg-[#1a1a2e] text-white rounded-[22px] rounded-br-none' 
              : 'bg-white text-[#1a1a2e] rounded-[22px] rounded-bl-none border border-white/60'"
          >
            <div v-if="msg.text.includes('**СОГЛАСОВАННОЕ ТЗ**')" class="whitespace-pre-wrap text-xs opacity-90 border-l-2 border-white/30 pl-3">
              {{ msg.text }}
            </div>
            <div v-else class="whitespace-pre-wrap">{{ msg.text }}</div>
            
            <div 
              class="text-[10px] mt-1.5 font-medium opacity-60 text-right w-full block select-none"
              :class="isMyMessage(msg) ? 'text-white/60' : 'text-gray-400'"
            >
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>
      </div>
  
      <div class="glass p-2 rounded-[26px] flex items-center gap-2 border border-white/60 shadow-xl relative z-20 bg-white/40 backdrop-blur-xl shrink-0">
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
          class="w-12 h-12 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 group"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        </button>
      </div>
  
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, nextTick } from 'vue'
  import { useRoute } from 'vue-router'
  import { useAuthStore } from '../stores/authStore'
  import axios from 'axios'
  
  const route = useRoute()
  const auth = useAuthStore()
  const messagesContainer = ref(null)
  
  const messages = ref([])
  const newMessage = ref('')
  const loading = ref(true)
  const isConnected = ref(false)
  const partner = ref(null)
  let socket = null
  
  const roomId = route.params.id
  
  const isMyMessage = (msg) => String(msg.sender_id) === String(auth.user.id)
  
  const formatTime = (isoString) => new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const getInitials = (name) => name ? name.substring(0, 1).toUpperCase() : '?'
  
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
  
  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}/`
    
    socket = new WebSocket(wsUrl)
  
    socket.onopen = () => { isConnected.value = true }
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'message') {
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
  
  onMounted(() => {
    fetchRoomDetails()
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
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 10px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(112, 0, 255, 0.3);
  }
  </style>