<template>
    <div class="min-h-screen pt-4 pb-20">
      
      <div class="text-center mb-12">
        <h1 class="text-4xl font-bold text-[#1a1a2e] mb-6 tracking-tight">Find the perfect service</h1>
        
        <div class="max-w-2xl mx-auto px-4 relative">
          <div class="glass p-2 rounded-full flex items-center shadow-xl transition-all focus-within:bg-white/20 focus-within:border-white/40 focus-within:shadow-2xl">
             <span class="pl-6 text-xl opacity-50">🔍</span>
             <input 
               v-model="searchQuery"
               @input="handleSearch"
               placeholder="What do you need done?" 
               class="w-full bg-transparent border-none outline-none text-lg p-4 placeholder-gray-500 text-[#1a1a2e] font-medium"
             >
             <button class="bg-[#1a1a2e] text-white px-8 py-3 rounded-full font-bold hover:bg-[#7000ff] transition-colors shadow-md mr-1">
               Search
             </button>
          </div>
        </div>
        
        <div class="flex justify-center gap-3 mt-8 flex-wrap px-4">
           <button v-for="cat in categories" :key="cat" class="px-5 py-2 rounded-full glass-chip text-sm font-bold text-gray-600 hover:bg-white/30 hover:text-[#1a1a2e] transition-all border border-white/20">
             {{ cat }}
           </button>
        </div>
      </div>
  
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
        
        <div 
          v-for="service in services" 
          :key="service.id" 
          class="glass rounded-[32px] p-6 hover:bg-white/20 transition-all cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1"
          @click="$router.push(`/services/${service.id}`)"
        >
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-xs font-bold border border-white/30 overflow-hidden">
               <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
               <span v-else>{{ getInitials(service.owner_name) }}</span>
            </div>
            <div class="flex-1 min-w-0">
               <div class="text-sm font-bold text-[#1a1a2e] truncate">{{ service.owner_name || 'Freelancer' }}</div>
               <div class="text-[10px] text-gray-500 font-bold uppercase">Level 1 Seller</div>
            </div>
            <div class="text-[#7000ff] font-bold text-lg">${{ service.price }}</div>
          </div>
  
          <h3 class="text-xl font-bold text-[#1a1a2e] mb-2 leading-tight group-hover:text-[#7000ff] transition-colors line-clamp-2">
            {{ service.title }}
          </h3>
          <p class="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-3 flex-1">
            {{ service.description }}
          </p>
  
          <div class="flex flex-wrap gap-2 mt-auto pt-4 border-t border-white/10">
             <span v-for="tag in service.tags?.slice(0,2)" :key="tag" class="px-3 py-1 rounded-lg bg-white/20 text-xs font-bold text-gray-600 border border-white/20">
               #{{ tag }}
             </span>
          </div>
        </div>
      </div>
      
      <div v-if="services.length === 0" class="text-center py-20 opacity-50">
         <div class="text-6xl mb-4">🌪️</div>
         <p class="font-bold">No services found.</p>
      </div>
  
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  
  const services = ref([])
  const searchQuery = ref('')
  const categories = ['Design', 'Development', 'Writing', 'Marketing', 'AI']
  
  const fetchServices = async () => {
    try {
      const res = await axios.get('/api/market/services/')
      if (res.data.status === 'success') {
        services.value = res.data.data
      } else if (Array.isArray(res.data)) {
        services.value = res.data
      }
    } catch (e) {
      console.error(e)
    }
  }
  
  const getInitials = (name) => {
    return name ? name.substring(0, 1).toUpperCase() : 'S'
  }
  
  const handleSearch = () => {
    console.log("Searching:", searchQuery.value)
  }
  
  onMounted(() => {
    fetchServices()
  })
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07), 0 8px 10px -6px rgba(0, 0, 0, 0.07);
  }
  
  .glass-chip {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
  }
  </style>