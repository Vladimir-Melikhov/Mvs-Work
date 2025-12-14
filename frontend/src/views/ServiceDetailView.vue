<template>
    <div class="animate-fade-in pb-20 pt-6">
      <button @click="$router.back()" class="mb-6 flex items-center gap-2 text-gray-500 hover:text-[#1a1a2e] transition-colors font-bold text-sm">
        ← Back
      </button>
  
      <div v-if="service" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div class="lg:col-span-2 space-y-6">
          <div class="glass p-8 rounded-[32px] border border-white/80 relative overflow-hidden">
            
            <div class="flex justify-between items-start mb-6">
               <h1 class="text-3xl font-bold text-[#1a1a2e] leading-tight">{{ service.title }}</h1>
            </div>
  
            <div class="flex flex-wrap gap-2 mb-8">
              <span v-for="tag in service.tags" :key="tag" class="px-3 py-1 rounded-lg bg-[#7000ff]/5 text-[#7000ff] text-xs font-bold uppercase tracking-wider">
                {{ tag }}
              </span>
            </div>
            
            <div class="prose max-w-none text-gray-600 leading-relaxed whitespace-pre-line">
              {{ service.description }}
            </div>
          </div>
        </div>
  
        <div class="space-y-6">
          <div class="glass p-8 rounded-[32px] border border-white/80 sticky top-24 shadow-sm">
            <div class="flex items-end gap-2 mb-1">
              <div class="text-4xl font-bold text-[#1a1a2e]">${{ service.price }}</div>
              <div class="text-gray-400 mb-1.5 font-medium">fixed price</div>
            </div>
            
            <div class="h-px bg-gray-100 my-6"></div>
  
            <div class="flex items-center gap-4 mb-6">
               <div class="w-12 h-12 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center font-bold text-gray-500">
                 ID
               </div>
               <div>
                 <div class="font-bold text-[#1a1a2e] text-sm">Owner ID:</div>
                 <div class="text-xs text-gray-500 font-mono">{{ service.owner_id.slice(0, 8) }}...</div>
               </div>
            </div>
  
            <button 
              @click="showWizard = true" 
              class="w-full bg-[#1a1a2e] text-white py-4 rounded-xl font-bold shadow-lg shadow-[#1a1a2e]/20 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2"
            >
              <span>Start Deal</span>
              <span class="text-xs bg-white/20 px-2 py-0.5 rounded text-white/90">AI Powered</span>
            </button>
          </div>
        </div>
      </div>
  
      <div v-else class="text-center py-20 text-gray-400 animate-pulse">
        Loading service details...
      </div>
  
      <AiDealWizard v-if="showWizard" :service="service" @close="showWizard = false" />
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import axios from 'axios'
  import AiDealWizard from '../components/AiDealWizard.vue'
  
  const route = useRoute()
  const service = ref(null)
  const showWizard = ref(false)
  
  const fetchService = async () => {
    try {
      // Используем реальный эндпоинт market service
      const res = await axios.get(`/api/market/services/${route.params.id}/`)
      service.value = res.data.data
    } catch (e) {
      console.error("Failed to load service", e)
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