<template>
  <div class="deals-history">
    <div class="flex flex-col gap-4 mb-6 px-2">
      <h3 class="text-xl font-bold text-[#1a1a2e]">История сделок</h3>
      
      <div class="flex gap-2">
        <button 
          v-for="tab in tabs" 
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-3 md:px-4 py-2 rounded-full text-xs md:text-sm font-bold transition-all"
          :class="activeTab === tab.value 
            ? 'bg-[#7000ff] text-white' 
            : 'bg-white/20 text-gray-600 hover:bg-white/40'"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-10 opacity-50">
      <div class="w-8 h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin mx-auto"></div>
    </div>

    <div v-else-if="paginatedDeals.length === 0" class="glass p-8 rounded-[32px] text-center border border-white/20 opacity-70">
      <div class="flex justify-center mb-3 opacity-30">
        <svg class="w-12 h-12 text-[#1a1a2e]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      </div>
      <p class="font-bold text-[#1a1a2e] mb-2">Сделок пока нет</p>
      <p class="text-sm text-gray-500">Начните общение с исполнителями или клиентами</p>
    </div>

    <div v-else>
      <div class="space-y-4">
        <div 
          v-for="deal in paginatedDeals" 
          :key="deal.id"
          class="glass rounded-[32px] p-4 md:p-6 hover:bg-white/20 transition-all border border-white/20 cursor-pointer"
          @click="$router.push(`/chats/${deal.chat_room_id}`)"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-8 md:w-10 h-8 md:h-10 rounded-2xl bg-white/30 flex items-center justify-center text-[#7000ff] shrink-0">
                  <svg v-if="deal.status === 'pending'" class="w-4 md:w-5 h-4 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else-if="deal.status === 'paid'" class="w-4 md:w-5 h-4 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <svg v-else-if="deal.status === 'delivered'" class="w-4 md:w-5 h-4 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  <svg v-else-if="deal.status === 'completed'" class="w-4 md:w-5 h-4 md:h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else-if="deal.status === 'cancelled'" class="w-4 md:w-5 h-4 md:h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <svg v-else class="w-4 md:w-5 h-4 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>

                <div class="flex-1 min-w-0">
                  <h4 class="text-base md:text-lg font-bold text-[#1a1a2e] break-words">{{ deal.title }}</h4>
                  <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                    {{ getStatusText(deal.status) }}
                  </div>
                </div>
              </div>
              <div class="text-xs md:text-sm text-gray-600 mt-2 line-clamp-2 break-words">
                {{ deal.description }}
              </div>
            </div>
            
            <div class="text-right ml-4 shrink-0">
              <div class="text-xl md:text-2xl font-bold" :class="getPriceColor(deal.status)">
                {{ deal.price }}₽
              </div>
              <div class="text-[10px] font-bold text-gray-400 mt-1 uppercase">
                {{ formatDate(deal.created_at) }}
              </div>
            </div>
          </div>

          <div class="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest pt-4 border-t border-white/10 flex-wrap">
            <span class="px-3 py-1 rounded-lg" :class="getRoleBadge(deal)">
              {{ getRole(deal) }}
            </span>
            
            <span v-if="['pending', 'paid', 'delivered'].includes(deal.status)" class="text-green-600 flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Активна
            </span>
            <span v-if="deal.status === 'completed'" class="text-blue-600 flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
              Завершена {{ formatDate(deal.completed_at) }}
            </span>
            <span v-if="deal.status === 'cancelled'" class="text-red-500 flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              Отменена
            </span>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex justify-center items-center gap-2 mt-6">
        <button 
          @click="currentPage--" 
          :disabled="currentPage === 1"
          class="w-9 h-9 rounded-full bg-white/20 hover:bg-white/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div class="flex gap-1">
          <button 
            v-for="page in visiblePages" 
            :key="page"
            @click="currentPage = page"
            class="w-9 h-9 rounded-full font-bold text-sm transition-all"
            :class="currentPage === page 
              ? 'bg-[#7000ff] text-white' 
              : 'bg-white/20 hover:bg-white/40 text-gray-700'"
          >
            {{ page }}
          </button>
        </div>

        <button 
          @click="currentPage++" 
          :disabled="currentPage === totalPages"
          class="w-9 h-9 rounded-full bg-white/20 hover:bg-white/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const auth = useAuthStore()

const deals = ref([])
const loading = ref(true)
const activeTab = ref('all')
const currentPage = ref(1)
const itemsPerPage = 5

const tabs = [
  { value: 'all', label: 'Все' },
  { value: 'active', label: 'Активные' },
  { value: 'completed', label: 'Завершенные' },
]

const filteredDeals = computed(() => {
  if (activeTab.value === 'all') return deals.value
  if (activeTab.value === 'active') return deals.value.filter(d => ['pending', 'paid', 'delivered'].includes(d.status))
  if (activeTab.value === 'completed') return deals.value.filter(d => d.status === 'completed')
  return deals.value
})

const totalPages = computed(() => Math.ceil(filteredDeals.value.length / itemsPerPage))

const paginatedDeals = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredDeals.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value
  
  if (total <= 5) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 3) {
      pages.push(1, 2, 3, 4, 5)
    } else if (current >= total - 2) {
      pages.push(total - 4, total - 3, total - 2, total - 1, total)
    } else {
      pages.push(current - 2, current - 1, current, current + 1, current + 2)
    }
  }
  
  return pages
})

// Reset page when tab changes
const previousTab = ref(activeTab.value)
const tabChanged = computed(() => {
  const changed = previousTab.value !== activeTab.value
  if (changed) {
    currentPage.value = 1
    previousTab.value = activeTab.value
  }
  return changed
})

const fetchDeals = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/market/deals/')
    if (res.data.status === 'success') {
      deals.value = res.data.data
    }
  } catch (e) {
    console.error('Failed to fetch deals:', e)
  } finally {
    loading.value = false
  }
}

const getRole = (deal) => {
  const isClient = String(auth.user.id) === String(deal.client_id)
  return isClient ? 'Заказчик' : 'Исполнитель'
}

const getRoleBadge = (deal) => {
  const isClient = String(auth.user.id) === String(deal.client_id)
  return isClient 
    ? 'bg-blue-50 text-blue-600 border border-blue-100' 
    : 'bg-green-50 text-green-700 border border-green-100'
}

const getStatusText = (status) => {
  const texts = {
    pending: 'Ожидает оплаты',
    paid: 'В работе',
    delivered: 'Сдано на проверку',
    completed: 'Завершена',
    cancelled: 'Отменена'
  }
  return texts[status] || status
}

const getPriceColor = (status) => {
  if (status === 'completed') return 'text-green-600'
  if (status === 'cancelled') return 'text-gray-400'
  if (['pending', 'paid', 'delivered'].includes(status)) return 'text-[#7000ff]'
  return 'text-gray-700'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

onMounted(() => {
  fetchDeals()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07);
}
</style>
