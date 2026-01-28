<template>
  <div class="min-h-screen pt-4 pb-20 animate-fade-in">
    
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold text-[#1a1a2e] tracking-tight">Сообщения</h1>
    </div>

    <div class="max-w-3xl mx-auto px-4">
      
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block w-8 h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
      </div>

      <div v-else-if="sortedChats.length > 0" class="space-y-4">
        <div 
          v-for="chat in sortedChats" 
          :key="chat.id" 
          class="glass p-4 rounded-[32px] flex items-center gap-4 cursor-pointer group hover:bg-white/20 transition-all active:scale-[0.98] relative"
          @click="openChat(chat.id)"
        >
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex-shrink-0 flex items-center justify-center text-white text-xl font-bold border border-white/20 shadow-md overflow-hidden relative">
            <img v-if="getPartner(chat).avatar" :src="getPartner(chat).avatar" class="w-full h-full object-cover">
            <span v-else>{{ getInitials(getPartner(chat).name) }}</span>
            
            <!-- Счетчик непрочитанных сообщений -->
            <div 
              v-if="chat.unread_count > 0" 
              class="absolute -top-1 -right-1 min-w-[24px] h-6 px-1.5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center shadow-lg border-2 border-white"
            >
              {{ chat.unread_count > 99 ? '99+' : chat.unread_count }}
            </div>
          </div>

          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-baseline mb-1">
              <h3 
                class="text-lg font-bold truncate"
                :class="chat.unread_count > 0 ? 'text-[#7000ff]' : 'text-[#1a1a2e]'"
              >
                {{ getPartner(chat).name || 'Loading...' }}
              </h3>
              <span class="text-xs text-gray-500 font-medium ml-2 shrink-0">
                {{ formatDate(chat.updated_at) }}
              </span>
            </div>
            <div 
              class="text-sm truncate group-hover:text-[#1a1a2e] transition-colors"
              :class="chat.unread_count > 0 ? 'text-[#1a1a2e] font-semibold' : 'text-gray-600'"
            >
              <span v-if="chat.last_message && String(chat.last_message.sender_id) === String(auth.user.id)" class="text-[#7000ff]">Вы: </span>
              <span v-html="formatLastMessage(chat.last_message)"></span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="glass p-12 rounded-[40px] text-center mt-8 border border-white/20">
        <div class="text-6xl mb-4 opacity-50">💬</div>
        <h3 class="text-xl font-bold text-[#1a1a2e] mb-2">Сообщений нет</h3>
        <p class="text-gray-500 mb-8 max-w-xs mx-auto"></p>
        
        <router-link 
          to="/search" 
          class="bg-[#1a1a2e] text-white px-8 py-3 rounded-full font-bold shadow-lg hover:bg-[#7000ff] transition-all inline-block"
        >
          Найти исполнителя
        </router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import { stripMarkdown } from '../utils/textUtils'

const router = useRouter()
const auth = useAuthStore()
const chats = ref([]) 
const loading = ref(false)
const usersMap = ref({})

// ✅ Сортировка чатов по времени последнего сообщения (новые сверху)
const sortedChats = computed(() => {
  return [...chats.value].sort((a, b) => {
    const dateA = new Date(a.updated_at || 0)
    const dateB = new Date(b.updated_at || 0)
    return dateB - dateA // Новые сверху
  })
})

const fetchChats = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/chat/rooms/')
    if (res.data.status === 'success') {
      chats.value = res.data.data
      await fetchUsersInfo(chats.value)
    }
  } catch (e) {
    console.warn("Could not fetch chats:", e)
    chats.value = []
  } finally {
    loading.value = false
  }
}

const fetchUsersInfo = async (rooms) => {
  const allMemberIds = new Set()
  
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
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'Только что'
  if (diffMins < 60) return `${diffMins} мин назад`
  if (diffHours < 24) return `${diffHours} ч назад`
  if (diffDays === 1) return 'Вчера'
  if (diffDays < 7) return `${diffDays} дн назад`
  
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const formatLastMessage = (message) => {
  if (!message || !message.text) {
    if (message && message.attachments && message.attachments.length > 0) {
      return '<span class="text-gray-500 italic">📎 Вложение</span>'
    }
    return 'No messages yet'
  }
  
  if (message.attachments && message.attachments.length > 0) {
    return '<span class="text-gray-500 italic">📎 Вложение</span>'
  }
  
  let text = stripMarkdown(message.text)

  const systemMarkers = ['📋', '💰', '📦', '🔄', '⚠️', '🛡️', '💳', '🎉', '❌']
  const isSystem = systemMarkers.some(marker => text.trim().startsWith(marker))
  
  if (!isSystem) return text
  
  const emojiMap = {
    '💰': { type: 'money', color: 'success' },
    '✅': { type: 'check', color: 'success' },
    '📦': { type: 'work', color: 'info' },
    '🔄': { type: 'clock', color: 'warning' },
    '🎉': { type: 'check', color: 'success' },
    '❌': { type: 'cancel', color: 'error' },
    '⚠️': { type: 'warning', color: 'warning' },
    '⏳': { type: 'clock', color: 'default' },
    '⚡': { type: 'lightning', color: 'purple' },
    '📋': { type: 'document', color: 'info' },
    '🛡️': { type: 'info', color: 'info' },
    '💳': { type: 'money', color: 'purple' }
  }
  
  Object.entries(emojiMap).forEach(([emoji, config]) => {
    const iconSvg = `<span class="inline-flex items-center align-middle mx-0.5">
      <svg class="w-3.5 h-3.5 ${getColorClass(config.color)}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        ${getIconPath(config.type)}
      </svg>
    </span>`
    
    text = text.replaceAll(emoji, iconSvg)
  })
  
  return text
}

const getColorClass = (color) => {
  const classes = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-orange-600',
    info: 'text-blue-600',
    purple: 'text-purple-600',
    default: 'text-gray-600'
  }
  return classes[color] || classes.default
}

const getIconPath = (type) => {
  const paths = {
    money: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v12M8 9h8M8 15h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    check: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>',
    work: '<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    cancel: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    warning: '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    clock: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    lightning: '<path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>',
    document: '<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    info: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 16v-4m0-4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
  }
  return paths[type] || paths.info
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
