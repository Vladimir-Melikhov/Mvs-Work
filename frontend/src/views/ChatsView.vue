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
            <div class="w-16 h-16 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex-shrink-0 flex items-center justify-center text-white text-xl font-bold border border-white/20 shadow-md">
              {{ chat.participant_initials || '?' }}
            </div>
  
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-baseline mb-1">
                <h3 class="text-lg font-bold text-[#1a1a2e] truncate">{{ chat.participant_name || 'User' }}</h3>
                <span class="text-xs text-gray-500 font-medium">{{ chat.last_message_time }}</span>
              </div>
              <p class="text-gray-600 text-sm truncate group-hover:text-[#1a1a2e] transition-colors">
                {{ chat.last_message || 'No messages yet' }}
              </p>
            </div>
  
            <div v-if="chat.unread_count" class="w-6 h-6 rounded-full bg-[#7000ff] flex items-center justify-center text-white text-[10px] font-bold shadow-lg shadow-[#7000ff]/30">
              {{ chat.unread_count }}
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
  
  const router = useRouter()
  const chats = ref([]) // Изначально пустой массив (без фейков)
  const loading = ref(false)
  
  const fetchChats = async () => {
    loading.value = true
    try {
      // Пытаемся получить реальные чаты
      // Если бэкенд не готов, вернется ошибка или пустота, и покажется "No messages yet"
      const res = await axios.get('/api/chat/conversations/')
      if (res.data.status === 'success') {
        chats.value = res.data.data
      }
    } catch (e) {
      console.warn("Could not fetch chats (Backend might be empty or not ready):", e)
      // Оставляем пустым, не добавляем фейки
      chats.value = []
    } finally {
      loading.value = false
    }
  }
  
  const openChat = (id) => {
    router.push(`/chats/${id}`)
  }
  
  onMounted(() => {
    fetchChats()
  })
  </script>
  
  <style scoped>
  /* Тот же стиль Crystal Glass, что и в Профиле/Шапке */
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    /* Легкая тень (shadow-lg shadow-black/5), как просили */
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  }
  </style>