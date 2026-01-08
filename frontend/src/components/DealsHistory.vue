<template>
  <div class="deals-history">
    <div class="flex items-center justify-between mb-6 px-2">
      <h3 class="text-xl font-bold text-[#1a1a2e]">История сделок</h3>
      <div class="flex gap-2">
        <button 
          v-for="tab in tabs" 
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-4 py-2 rounded-full text-sm font-bold transition-all"
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

    <div v-else-if="filteredDeals.length === 0" class="glass p-8 rounded-[32px] text-center border border-white/20 opacity-70">
      <div class="text-5xl mb-3 opacity-30">📋</div>
      <p class="font-bold text-[#1a1a2e] mb-2">Сделок пока нет</p>
      <p class="text-sm text-gray-500">Начните общение с исполнителями или клиентами</p>
    </div>

    <div v-else class="space-y-4">
      <div 
        v-for="deal in filteredDeals" 
        :key="deal.id"
        class="glass rounded-[32px] p-6 hover:bg-white/20 transition-all border border-white/20 cursor-pointer"
        @click="$router.push(`/chats/${deal.chat_room_id}`)"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-2xl">{{ getStatusIcon(deal.status) }}</span>
              <div>
                <h4 class="text-lg font-bold text-[#1a1a2e]">{{ deal.title }}</h4>
                <div class="text-xs text-gray-500">
                  {{ getStatusText(deal.status) }}
                </div>
              </div>
            </div>
            <div class="text-sm text-gray-600 mt-2 line-clamp-2">
              {{ deal.description }}
            </div>
          </div>
          
          <div class="text-right ml-4">
            <div class="text-2xl font-bold" :class="getPriceColor(deal.status)">
              {{ deal.price }}₽
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ formatDate(deal.created_at) }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3 text-xs pt-3 border-t border-white/20">
          <span class="px-3 py-1 rounded-full" :class="getRoleBadge(deal)">
            {{ getRole(deal) }}
          </span>
          
          <span v-if="['pending', 'paid', 'delivered'].includes(deal.status)" class="text-green-600 font-bold">
            ✅ Активна
          </span>
          <span v-if="deal.status === 'completed'" class="text-blue-600 font-bold">
            🎉 Завершена {{ formatDate(deal.completed_at) }}
          </span>
          <span v-if="deal.status === 'cancelled'" class="text-red-600 font-bold">
            ❌ Отменена
          </span>
        </div>
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

const tabs = [
  { value: 'all', label: 'Все' },
  { value: 'active', label: 'Активные' },
  { value: 'completed', label: 'Завершенные' },
]

// ✅ ИСПРАВЛЕНО: правильные статусы
const filteredDeals = computed(() => {
  if (activeTab.value === 'all') return deals.value
  if (activeTab.value === 'active') return deals.value.filter(d => ['pending', 'paid', 'delivered'].includes(d.status))
  if (activeTab.value === 'completed') return deals.value.filter(d => d.status === 'completed')
  return deals.value
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
  return isClient ? 'Я — Клиент' : 'Я — Исполнитель'
}

const getRoleBadge = (deal) => {
  const isClient = String(auth.user.id) === String(deal.client_id)
  return isClient 
    ? 'bg-blue-100 text-blue-700 font-bold' 
    : 'bg-green-100 text-green-700 font-bold'
}

const getStatusIcon = (status) => {
  const icons = {
    pending: '⏳',
    paid: '⚙️',
    delivered: '📦',
    completed: '🎉',
    cancelled: '❌'
  }
  return icons[status] || '📋'
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