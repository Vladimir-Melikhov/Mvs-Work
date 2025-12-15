<template>
    <div class="animate-fade-in pb-20 pt-6">
      <button @click="$router.back()" class="mb-6 flex items-center gap-2 text-gray-500 hover:text-[#7000ff] transition-colors font-medium ml-4">
        ← Назад к поиску
      </button>
  
      <div v-if="service" class="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto px-4">
        
        <div class="lg:col-span-2 space-y-6">
          <div class="glass p-8 rounded-3xl border border-white/80">
            <div class="flex justify-between items-start mb-6">
               <h1 class="text-3xl font-bold text-[#1a1a2e]">{{ service.title }}</h1>
               <span class="bg-[#7000ff]/10 text-[#7000ff] px-4 py-1 rounded-full text-sm font-bold">
                 {{ service.category || 'Development' }}
               </span>
            </div>
            
            <div class="prose max-w-none text-gray-600 leading-relaxed whitespace-pre-line mb-8">
              {{ service.description }}
            </div>
  
            <div class="flex flex-wrap gap-2">
              <span v-for="tag in service.tags" :key="tag" class="px-4 py-2 rounded-xl bg-gray-100 text-gray-600 text-sm font-medium">
                #{{ tag }}
              </span>
            </div>
          </div>
        </div>
  
        <div class="space-y-6">
          <div class="glass p-6 rounded-3xl border border-white/80 sticky top-24">
            <div class="text-3xl font-bold text-[#7000ff] mb-2">${{ service.price }}</div>
            <p class="text-gray-400 text-sm mb-6">Фиксированная цена</p>
            
            <div v-if="isOwner" class="space-y-3">
              <div class="p-3 bg-yellow-50 border border-yellow-100 rounded-xl text-xs text-yellow-800 font-bold text-center mb-4">
                 🛠 Это ваше объявление
              </div>
  
              <button 
                @click="$router.push(`/my-services/edit/${service.id}`)" 
                class="w-full bg-gray-100 text-[#1a1a2e] py-3 rounded-xl font-bold hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
              >
                ✏️ Редактировать
              </button>
  
              <button 
                @click="deleteService" 
                class="w-full bg-red-50 text-red-500 border border-red-100 py-3 rounded-xl font-bold hover:bg-red-500 hover:text-white transition-all flex items-center justify-center gap-2"
              >
                🗑 Удалить
              </button>
            </div>
  
            <div v-else>
              <button 
                @click="showWizard = true" 
                class="w-full bg-gradient-to-r from-[#7000ff] to-[#00c6ff] text-white py-4 rounded-xl font-bold shadow-lg shadow-[#7000ff]/25 hover:scale-[1.02] transition-transform"
              >
                Start Deal with AI
              </button>
              
              <div class="mt-6 pt-6 border-t border-gray-100 flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-xl font-bold text-gray-500 overflow-hidden">
                   <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
                   <span v-else>{{ service.owner_id ? service.owner_id.slice(0,2).toUpperCase() : 'U' }}</span>
                </div>
                <div>
                  <div class="font-bold text-[#1a1a2e]">{{ service.owner_name || 'User' }}</div>
                  <div class="text-xs text-green-500 font-medium">● Online</div>
                </div>
              </div>
            </div>
            </div>
        </div>
      </div>
  
      <AiDealWizard v-if="showWizard" :service="service" @close="showWizard = false" />
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import axios from 'axios'
  import AiDealWizard from '../components/AiDealWizard.vue'
  
  const route = useRoute()
  const router = useRouter()
  const service = ref(null)
  const showWizard = ref(false)
  
  // Получаем ID текущего юзера из localStorage (стандартная практика для MVP)
  const currentUserId = localStorage.getItem('user_id')
  
  // Вычисляем, является ли юзер владельцем
  const isOwner = computed(() => {
    if (!service.value || !currentUserId) return false
    // Сравниваем как строки, чтобы избежать проблем с типами
    return String(service.value.owner_id) === String(currentUserId)
  })
  
  const fetchService = async () => {
    try {
      const res = await axios.get(`/api/market/services/${route.params.id}/`)
      service.value = res.data.data
    } catch (e) {
      console.error("Failed to fetch service")
    }
  }
  
  // Функция удаления
  const deleteService = async () => {
    if (!confirm('Вы уверены, что хотите удалить эту услугу? Это действие нельзя отменить.')) return
  
    try {
      await axios.delete(`/api/market/services/${service.value.id}/`)
      alert('Услуга удалена')
      router.push('/market') // Перенаправляем в общий каталог
    } catch (e) {
      console.error(e)
      alert('Ошибка при удалении: ' + (e.response?.data?.error || 'Нет прав'))
    }
  }
  
  onMounted(fetchService)
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(15px);
  }
  </style>