<template>
    <div class="min-h-screen pt-4 pb-20 animate-fade-in">
      
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-[#1a1a2e] tracking-tight">Messages</h1>
      </div>
  
      <div class="max-w-3xl mx-auto px-4">
        
        <div v-if="loading" class="text-center py-12">
          <div class="inline-block w-8 h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
        </div>
  
        <div v-else-if="chats.length > 0" class="space-y-4">
          <div 
            v-for="chat in chats" 
            :key="chat.id" 
            class="glass p-4 rounded-[32px] flex items-center gap-4 cursor-pointer group hover:bg-white/20 transition-all active:scale-[0.98]"
            @click="openChat(chat.id)"
          >
            <div class="w-16 h-16 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex-shrink-0 flex items-center justify-center text-white text-xl font-bold border border-white/20 shadow-md overflow-hidden">
              <img v-if="getPartner(chat).avatar" :src="getPartner(chat).avatar" class="w-full h-full object-cover">
              <span v-else>{{ getInitials(getPartner(chat).name) }}</span>
            </div>
  
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-baseline mb-1">
                <h3 class="text-lg font-bold text-[#1a1a2e] truncate">
                  {{ getPartner(chat).name || 'Loading...' }}
                </h3>
                <span class="text-xs text-gray-500 font-medium">
                  {{ formatDate(chat.updated_at) }}
                </span>
              </div>
              <p class="text-gray-600 text-sm truncate group-hover:text-[#1a1a2e] transition-colors">
                <span v-if="chat.last_message && String(chat.last_message.sender_id) === String(auth.user.id)" class="text-[#7000ff]">You: </span>
                {{ chat.last_message ? chat.last_message.text : 'No messages yet' }}
              </p>
            </div>
          </div>
        </div>
  
        <div v-else class="glass p-12 rounded-[40px] text-center mt-8 border border-white/20">
          <div class="text-6xl mb-4 opacity-50">💬</div>
          <h3 class="text-xl font-bold text-[#1a1a2e] mb-2">No messages yet</h3>
          <p class="text-gray-500 mb-8 max-w-xs mx-auto">Connect with freelancers or clients to start a conversation.</p>
          
          <router-link 
            to="/search" 
            class="bg-[#1a1a2e] text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-[#7000ff] transition-all inline-block"
          >
            Find Services
          </router-link>
        </div>
  
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '../stores/authStore'
  
  const router = useRouter()
  const auth = useAuthStore()
  const chats = ref([]) 
  const loading = ref(false)
  const usersMap = ref({}) // Кэш пользователей { id: {name, avatar} }
  
  const fetchChats = async () => {
    loading.value = true
    try {
      const res = await axios.get('/api/chat/rooms/')
      if (res.data.status === 'success') {
        chats.value = res.data.data
        // После загрузки чатов, загружаем инфу о людях
        await fetchUsersInfo(chats.value)
      }
    } catch (e) {
      console.warn("Could not fetch chats:", e)
      chats.value = []
    } finally {
      loading.value = false
    }
  }
  
  // Загрузка имен из Auth сервиса
  const fetchUsersInfo = async (rooms) => {
    const allMemberIds = new Set()
    
    // Собираем ID всех собеседников (исключая себя)
    rooms.forEach(room => {
        room.members.forEach(id => {
            if (String(id) !== String(auth.user.id)) {
                allMemberIds.add(id)
            }
        })
    })

    if (allMemberIds.size === 0) return

    try {
        const res = await axios.post('/api/auth/users/batch/', {
            user_ids: Array.from(allMemberIds)
        })
        
        if (res.data.status === 'success') {
            res.data.data.forEach(user => {
                usersMap.value[user.id] = user
            })
        }
    } catch (e) {
        console.error("Failed to fetch users info:", e)
    }
  }
  
  const openChat = (id) => {
    router.push(`/chats/${id}`)
  }

  // Получить объект собеседника для конкретного чата
  const getPartner = (chat) => {
    const partnerId = chat.members.find(id => String(id) !== String(auth.user.id))
    if (!partnerId) return { name: 'Saved Messages' }
    
    return usersMap.value[partnerId] || { name: 'User...', avatar: null }
  }

  const getInitials = (name) => {
    return name ? name.substring(0, 1).toUpperCase() : '?'
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  onMounted(() => {
    fetchChats()
  })
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  }
  </style>