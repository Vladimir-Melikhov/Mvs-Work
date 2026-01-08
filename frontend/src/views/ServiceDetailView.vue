<template>
    <div class="animate-fade-in pb-20 pt-6">
      <button @click="$router.back()" class="mb-6 flex items-center gap-2 text-gray-500 hover:text-[#7000ff] transition-colors font-medium ml-4">
        ← Назад
      </button>
  
      <div v-if="service" class="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto px-4">
        
        <div class="lg:col-span-2 space-y-6">
          <div class="glass p-8 rounded-[40px] border border-white/20">
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
              <span v-for="tag in service.tags" :key="tag" class="px-4 py-2 rounded-xl bg-gray-100/50 text-gray-600 text-sm font-medium border border-white/20">
                #{{ tag }}
              </span>
            </div>
          </div>
        </div>
  
        <div class="space-y-6">
          <div class="glass p-8 rounded-[40px] border border-white/20 sticky top-24">
            <div class="text-3xl font-bold text-[#7000ff] mb-2">{{ service.price }} ₽</div>
            <p class="text-gray-400 text-sm mb-6">Начальная цена</p>
            
            <div v-if="isOwner" class="space-y-3">
               <div class="p-4 rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md flex items-center gap-3 mb-4 shadow-sm">
                 <div class="w-8 h-8 rounded-full bg-[#1a1a2e] flex items-center justify-center text-white">
                   <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                   </svg>
                 </div>
                 <span class="text-xs font-bold text-[#1a1a2e] uppercase tracking-wider">Это ваше объявление</span>
               </div>
               
               <button 
                 @click="$router.push(`/my-services/edit/${service.id}`)" 
                 class="w-full py-3.5 rounded-2xl font-bold flex items-center justify-center gap-2 border border-white/20 bg-white/10 hover:bg-white/20 transition-all text-[#1a1a2e] shadow-lg shadow-black/5"
               >
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                 </svg>
                 <span>Редактировать</span>
               </button>
  
               <button 
                 @click="deleteService" 
                 class="w-full py-3.5 rounded-2xl font-bold flex items-center justify-center gap-2 border border-red-500/20 bg-red-500/5 hover:bg-red-500 hover:text-white hover:border-red-500 transition-all text-red-500 shadow-lg shadow-red-500/5"
               >
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                 </svg>
                 <span>Удалить</span>
               </button>
            </div>
  
            <div v-else>
              <button 
                @click="showWizard = true" 
                class="w-full bg-[#1a1a2e] text-white py-4 rounded-2xl font-bold shadow-xl shadow-[#1a1a2e]/20 hover:bg-[#7000ff] hover:shadow-[#7000ff]/25 hover:scale-[1.02] transition-all flex justify-center items-center gap-2"
              >
                <span></span> Начать сделку с AI
              </button>
              
              <div class="mt-8 pt-6 border-t border-white/20 flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-xl font-bold text-gray-500 overflow-hidden border border-white/30">
                   <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
                   <span v-else>{{ service.owner_id ? service.owner_id.slice(0,2).toUpperCase() : 'U' }}</span>
                </div>
                <div>
                  <div class="font-bold text-[#1a1a2e]">{{ service.owner_name || 'Пользователь' }}</div>
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
  import { useAuthStore } from '../stores/authStore'
  import axios from 'axios'
  import AiDealWizard from '../components/AiDealWizard.vue'
  
  const route = useRoute()
  const router = useRouter()
  const auth = useAuthStore()
  const service = ref(null)
  const showWizard = ref(false)
  
  const isOwner = computed(() => {
    if (!service.value || !auth.user) return false
    return String(service.value.owner_id) === String(auth.user.id)
  })
  
  const fetchService = async () => {
    try {
      const res = await axios.get(`/api/market/services/${route.params.id}/`)
      service.value = res.data.data
    } catch (e) {
      console.error("Failed to fetch service")
    }
  }
  
  const deleteService = async () => {
    if (!confirm('Вы уверены, что хотите удалить эту услугу? Это действие нельзя отменить.')) return
  
    try {
      await axios.delete(`/api/market/services/${service.value.id}/`)
      alert('Услуга успешно удалена')
      router.push('/profile')
    } catch (e) {
      console.error(e)
      alert('Ошибка при удалении: ' + (e.response?.data?.error || 'Нет прав'))
    }
  }
  
  onMounted(async () => {
    if (!auth.user) {
      await auth.fetchProfile()
    }
    fetchService()
  })
  </script>
  
  <style scoped>
  /* СТИЛЬ СТЕКЛА (как в профиле) */
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07), 0 8px 10px -6px rgba(0, 0, 0, 0.07);
  }
  </style>
