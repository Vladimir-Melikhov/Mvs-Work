<template>
  <!-- DESKTOP VERSION -->
  <div class="hidden md:flex h-[calc(100vh-150px)] gap-4 max-w-7xl mx-auto pt-4 pb-2 px-4">
    
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Шапка чата -->
      <div class="glass px-6 py-3 rounded-[24px] flex items-center gap-4 mb-3 border border-white/60 shadow-sm shrink-0">
        <button 
          @click="$router.push('/chats')" 
          class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold"
        >
          ←
        </button>
        
        <div 
          class="cursor-pointer hover:ring-2 hover:ring-[#7000ff] rounded-full transition-all"
          @click="goToPartnerProfile"
        >
          <UserAvatar 
            :avatar-url="partner?.avatar"
            :name="partner?.name || 'U'"
            size="lg"
            class="ring-2 ring-white/50 shadow-md"
          />
        </div>
        
        <div class="flex-1">
          <h2 
            class="text-lg font-bold text-[#1a1a2e] cursor-pointer hover:text-[#7000ff] transition-colors"
            @click="goToPartnerProfile"
          >
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
            class="max-w-[75%] px-5 py-3 text-[15px] leading-relaxed shadow-sm break-words"
            :class="isMyMessage(msg) 
              ? 'bg-[#1a1a2e] text-white rounded-[22px] rounded-br-none' 
              : 'bg-white text-[#1a1a2e] rounded-[22px] rounded-bl-none border border-white/60'"
          >
            <div 
              class="whitespace-pre-wrap" 
              v-html="formatMessageText(msg.text, ['📋', '💰', '📦', '🔄', '⚠️', '🛡️', '💳', '🎉', '❌'].some(m => msg.text.startsWith(m)))"
            ></div>
            
            <!-- Вложения -->
            <div v-if="msg.attachments && msg.attachments.length > 0" class="mt-2 space-y-2">
              <a 
                v-for="(att, idx) in msg.attachments" 
                :key="idx"
                :href="att.url" 
                target="_blank"
                class="flex items-center gap-2 p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-sm"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                <span class="truncate">{{ att.name }}</span>
              </a>
            </div>
            
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
        <label class="cursor-pointer w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/40 transition-all">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <input 
            type="file" 
            multiple
            @change="handleFileSelect"
            class="hidden"
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.zip,.rar"
          >
        </label>
        
        <input 
          v-model="newMessage" 
          @keydown.enter="sendMessage"
          type="text" 
          placeholder="Напишите сообщение..." 
          class="flex-1 bg-transparent border-none outline-none px-6 py-3.5 text-[#1a1a2e] placeholder-gray-500 font-medium text-[15px]"
        >
        <button 
          @click="sendMessage"
          :disabled="(!newMessage.trim() && selectedFiles.length === 0) || !isConnected || uploading"
          class="w-12 h-12 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] hover:scale-105 transition-all disabled:opacity-50"
        >
          <svg v-if="!uploading" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          <div v-else class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </div>
      
      <!-- Превью выбранных файлов -->
      <div v-if="selectedFiles.length > 0" class="mt-2 flex flex-wrap gap-2">
        <div 
          v-for="(file, idx) in selectedFiles" 
          :key="idx"
          class="flex items-center gap-2 px-3 py-1 bg-white/60 rounded-full text-sm"
        >
          <span class="truncate max-w-[150px]">{{ file.name }}</span>
          <button @click="removeFile(idx)" class="text-red-500 hover:text-red-700">×</button>
        </div>
      </div>
    </div>

    <div class="w-96 shrink-0 overflow-y-auto pr-2 scrollbar-thin">
      <div class="mb-4">
        <a 
          :href="supportLink" 
          target="_blank"
          rel="noopener noreferrer"
          class="glass flex items-center gap-3 p-4 rounded-[24px] border border-white/40 hover:bg-white/20 transition-all group"
        >
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#7000ff] to-[#5500cc] flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-bold text-[#1a1a2e] group-hover:text-[#7000ff] transition-colors">
              Служба поддержки
            </div>
            <div class="text-xs text-gray-500">Нужна помощь? Напишите нам</div>
          </div>
          <svg class="w-4 h-4 text-gray-400 group-hover:text-[#7000ff] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
      
      <div v-if="activeDeals.length === 0" class="glass rounded-[32px] p-6 border border-white/40 flex flex-col items-center justify-center text-center min-h-[300px]">
        <div class="text-5xl mb-3 opacity-30">📋</div>
        <p class="text-sm text-gray-500 mb-4">Заказов пока нет</p>
      </div>

      <div v-else class="space-y-3 pb-4">
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

  <!-- MOBILE VERSION - Полноэкранная -->
  <div class="md:hidden flex flex-col" style="height: 100vh; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: #f2f4f8;">
    
    <!-- Шапка чата -->
    <div class="glass px-3 py-2 rounded-b-[24px] flex items-center gap-2 border-b border-white/60 shadow-sm shrink-0">
      <button 
        @click="$router.push('/chats')" 
        class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold"
      >
        ←
      </button>
      
      <div 
        class="cursor-pointer"
        @click="goToPartnerProfile"
      >
        <UserAvatar 
          :avatar-url="partner?.avatar"
          :name="partner?.name || 'U'"
          size="sm"
          class="ring-2 ring-white/50 shadow-md"
        />
      </div>
      
      <div class="flex-1 min-w-0">
        <h2 
          class="text-sm font-bold text-[#1a1a2e] truncate cursor-pointer"
          @click="goToPartnerProfile"
        >
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
      
      <button 
        @click="mobileShowSupport = !mobileShowSupport"
        class="w-9 h-9 flex items-center justify-center rounded-full transition-all font-bold"
        :class="mobileShowSupport ? 'bg-[#7000ff] text-white' : 'bg-white/40 text-[#1a1a2e]'"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
        </svg>
      </button>
    </div>

    <!-- Служба поддержки -->
    <div v-if="mobileShowSupport" class="p-3 shrink-0">
      <a 
        :href="supportLink" 
        target="_blank"
        rel="noopener noreferrer"
        class="glass flex items-center gap-3 p-3 rounded-[20px] border border-white/40 hover:bg-white/20 transition-all"
      >
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#7000ff] to-[#5500cc] flex items-center justify-center shrink-0">
          <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-bold text-[#1a1a2e]">Служба поддержки</div>
          <div class="text-xs text-gray-500">Нужна помощь? Напишите нам</div>
        </div>
      </a>
    </div>

    <!-- Основной контент -->
    <div v-if="!mobileShowDeal" class="flex-1 flex flex-col min-h-0 px-2">
      <div 
        ref="messagesContainer"
        class="flex-1 glass rounded-[28px] p-3 overflow-y-auto space-y-2 my-2 border border-white/40 scroll-smooth"
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
            class="max-w-[85%] px-3 py-2 text-sm leading-relaxed shadow-sm break-words"
            :class="isMyMessage(msg) 
              ? 'bg-[#1a1a2e] text-white rounded-[18px] rounded-br-none' 
              : 'bg-white text-[#1a1a2e] rounded-[18px] rounded-bl-none border border-white/60'"
          >
            <div 
              class="whitespace-pre-wrap" 
              v-html="formatMessageText(msg.text, ['📋', '💰', '📦', '🔄', '⚠️', '🛡️', '💳', '🎉', '❌'].some(m => msg.text.startsWith(m)))"
            ></div>
            
            <!-- Вложения -->
            <div v-if="msg.attachments && msg.attachments.length > 0" class="mt-2 space-y-1">
              <a 
                v-for="(att, idx) in msg.attachments" 
                :key="idx"
                :href="att.url" 
                target="_blank"
                class="flex items-center gap-2 p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-xs"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                <span class="truncate">{{ att.name }}</span>
              </a>
            </div>
            
            <div 
              class="text-[9px] mt-1 font-medium opacity-60 text-right"
              :class="isMyMessage(msg) ? 'text-white/60' : 'text-gray-400'"
            >
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <div class="glass p-1.5 rounded-[22px] flex items-center gap-1.5 border border-white/60 shadow-xl bg-white/40 backdrop-blur-xl shrink-0 mb-2">
        <label class="cursor-pointer w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/40 transition-all shrink-0">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <input 
            type="file" 
            multiple
            @change="handleFileSelect"
            class="hidden"
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.zip,.rar"
          >
        </label>
        
        <input 
          v-model="newMessage" 
          @keydown.enter="sendMessage"
          type="text" 
          placeholder="Сообщение..." 
          class="flex-1 bg-transparent border-none outline-none px-3 py-2.5 text-[#1a1a2e] placeholder-gray-500 font-medium text-sm min-w-0"
        >
        <button 
          @click="sendMessage"
          :disabled="(!newMessage.trim() && selectedFiles.length === 0) || !isConnected || uploading"
          class="w-9 h-9 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] transition-all disabled:opacity-50 shrink-0"
        >
          <svg v-if="!uploading" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          <div v-else class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </div>
      
      <!-- Превью выбранных файлов (мобильная) -->
      <div v-if="selectedFiles.length > 0" class="mb-2 flex flex-wrap gap-1">
        <div 
          v-for="(file, idx) in selectedFiles" 
          :key="idx"
          class="flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full text-xs"
        >
          <span class="truncate max-w-[100px]">{{ file.name }}</span>
          <button @click="removeFile(idx)" class="text-red-500 hover:text-red-700 text-sm">×</button>
        </div>
      </div>
    </div>

    <!-- Список заказов (мобильная) -->
    <div v-else class="flex-1 overflow-y-auto p-2">
      <div v-if="activeDeals.length === 0" class="glass rounded-[32px] p-6 border border-white/40 flex flex-col items-center justify-center text-center h-full">
        <div class="text-5xl mb-3 opacity-30">📋</div>
        <p class="text-sm text-gray-500 mb-4">Заказов пока нет</p>
      </div>

      <div v-else class="space-y-2">
        <div 
          v-for="(deal, index) in activeDeals" 
          :key="deal.deal_id"
          class="glass rounded-[24px] border border-white/40 overflow-hidden"
        >
          <div 
            @click="toggleDeal(index)"
            class="p-3 cursor-pointer hover:bg-white/20 transition-all flex items-center justify-between"
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import axios from 'axios'
import DealMessage from '../components/DealMessage.vue'
import UserAvatar from '../components/UserAvatar.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const messagesContainer = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const isConnected = ref(false)
const partner = ref(null)
const mobileShowDeal = ref(false)
const mobileShowSupport = ref(false)
const expandedDealIndex = ref(0)
const selectedFiles = ref([])
const uploading = ref(false)

let socket = null
const roomId = route.params.id

const supportLink = computed(() => {
  const botUsername = import.meta.env.VITE_SUPPORT_BOT_USERNAME || 'your_support_bot'
  return `https://t.me/${botUsername}`
})

const textMessages = computed(() => {
  return messages.value.filter(m => m.message_type === 'text')
})

const dealMessages = computed(() => {
  return messages.value.filter(m => m.message_type !== 'text')
})

const activeDeals = computed(() => {
  return dealMessages.value
    .map(m => m.deal_data)
    .filter(d => d && d.deal_id)
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
})

const isMyMessage = (msg) => String(msg.sender_id) === String(auth.user.id)
const formatTime = (isoString) => new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const formatMessageText = (text, isSystem = false) => {
  if (!text) return ''
  
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
  
  let formatted = text
  
  Object.entries(emojiMap).forEach(([emoji, config]) => {
    const iconSvg = `<span class="inline-flex items-center align-middle mx-1">
      <svg class="w-5 h-5 ${getColorClass(config.color)}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        ${getIconPath(config.type)}
      </svg>
    </span>`
    
    formatted = formatted.replaceAll(emoji, iconSvg)
  })
  
  return formatted
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

const goToPartnerProfile = () => {
  const partnerId = partner.value?.id
  if (partnerId) {
    router.push(`/users/${partnerId}`)
  }
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  
  // Валидация файлов
  const validFiles = files.filter(file => {
    // Максимум 20MB для обычных сообщений
    if (file.size > 20 * 1024 * 1024) {
      alert(`Файл ${file.name} слишком большой (макс 20MB)`)
      return false
    }
    return true
  })
  
  selectedFiles.value.push(...validFiles)
  event.target.value = '' // Сброс input
}

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) return []
  
  const formData = new FormData()
  selectedFiles.value.forEach(file => {
    formData.append('files', file)
  })
  
  try {
    const res = await axios.post('/api/chat/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.data.status === 'success') {
      return res.data.data.files
    }
  } catch (e) {
    console.error('Upload error:', e)
    throw new Error('Ошибка загрузки файлов')
  }
  
  return []
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
      partner.value = {
        ...userRes.data.data[0],
        id: partnerId
      }
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

const sendMessage = async () => {
  if ((!newMessage.value.trim() && selectedFiles.value.length === 0) || !isConnected.value || uploading.value) return
  
  try {
    uploading.value = true
    
    // Загружаем файлы если есть
    let attachments = []
    if (selectedFiles.value.length > 0) {
      attachments = await uploadFiles()
    }
    
    // Отправляем сообщение через WebSocket
    socket.send(JSON.stringify({ 
      type: 'message', 
      sender_id: auth.user.id, 
      text: newMessage.value,
      attachments: attachments
    }))
    
    newMessage.value = ''
    selectedFiles.value = []
  } catch (e) {
    alert('Ошибка отправки: ' + e.message)
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  fetchRoomDetails()
  fetchHistory()
  connectWebSocket()
})
onUnmounted(() => { if (socket) socket.close() })
</script>

<style scoped>
.glass { 
  background: rgba(255, 255, 255, 0.7); 
  backdrop-filter: blur(30px); 
}

@keyframes scale-in { 
  from { opacity: 0; transform: scale(0.98); } 
  to { opacity: 1; transform: scale(1); } 
}

.animate-scale-in { 
  animation: scale-in 0.15s ease forwards; 
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