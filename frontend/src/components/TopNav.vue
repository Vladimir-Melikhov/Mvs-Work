<template>
  <div class="fixed top-6 left-0 right-0 z-50 px-4 flex justify-center">
    
    <nav class="w-full max-w-[1200px] h-[70px] bg-white/10 backdrop-blur-3xl border border-white/20 rounded-full flex items-center px-8 justify-between shadow-lg shadow-black/5 transition-all hover:bg-white/20">
      
      <router-link to="/" class="flex flex-col items-start leading-none group select-none">
        <span class="text-[19px] font-medium text-[#1a1a2e] ml-[0px] mb-[-4px] opacity-80 group-hover:opacity-100 transition-opacity">
          Mvs
        </span>
        <span class="text-3xl font-black text-[#1a1a2e] tracking-tighter transform scale-x-125 origin-left hover:opacity-80 transition-opacity">
          Work
        </span>
      </router-link>

      <div class="flex items-center gap-2">
        <router-link 
          to="/search" 
          class="px-6 py-2.5 rounded-full text-gray-700 font-semibold text-sm transition-all hover:bg-white/10 hover:text-[#1a1a2e]" 
          active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] shadow-inner backdrop-blur-md"
        >
          Поиск
        </router-link>
        
        <router-link 
          to="/chats" 
          class="px-6 py-2.5 rounded-full text-gray-700 font-semibold text-sm transition-all hover:bg-white/10 hover:text-[#1a1a2e]" 
          active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] shadow-inner backdrop-blur-md"
        >
          Чаты
        </router-link>
        
        <router-link 
          to="/profile" 
          class="px-6 py-2.5 rounded-full text-gray-700 font-semibold text-sm transition-all hover:bg-white/10 hover:text-[#1a1a2e]" 
          active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] shadow-inner backdrop-blur-md"
        >
          Профиль
        </router-link>

        <router-link 
          v-if="isWorker"
          to="/create-service" 
          class="ml-4 w-10 h-10 rounded-full bg-[#1a1a2e] text-white flex items-center justify-center shadow-md hover:bg-[#7000ff] hover:scale-105 transition-all border border-white/10"
          title="Create Service"
        >
          <span class="text-xl font-light mb-0.5">+</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/authStore'

const auth = useAuthStore()
const isWorker = computed(() => auth.user?.role === 'worker')
</script>