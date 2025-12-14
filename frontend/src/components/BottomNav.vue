<template>
    <div class="fixed bottom-8 left-4 right-4 z-50 flex justify-center">
      
      <nav class="w-full max-w-[380px] bg-white/10 backdrop-blur-3xl border border-white/20 rounded-full p-2 px-6 flex justify-between items-center shadow-lg shadow-black/5">
        
        <router-link 
          to="/search" 
          class="flex flex-col items-center justify-center w-12 h-12 rounded-full text-gray-500 transition-all hover:bg-white/10"
          active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] backdrop-blur-md shadow-sm"
        >
          <span class="text-xl">🔍</span>
        </router-link>
        
        <router-link 
          v-if="isWorker"
          to="/create-service"
          class="flex items-center justify-center w-12 h-12 rounded-full bg-[#1a1a2e] text-white shadow-md border border-white/10 hover:scale-105 transition-transform"
        >
          <span class="text-2xl font-light mb-1">+</span>
        </router-link>
        
        <router-link 
          to="/chats" 
          class="flex flex-col items-center justify-center w-12 h-12 rounded-full text-gray-500 transition-all hover:bg-white/10"
          active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] backdrop-blur-md shadow-sm"
        >
          <span class="text-xl">💬</span>
        </router-link>
        
        <router-link 
          to="/profile" 
          class="flex flex-col items-center justify-center w-12 h-12 rounded-full text-gray-500 transition-all hover:bg-white/10"
          active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] backdrop-blur-md shadow-sm"
        >
          <span class="text-xl">👤</span>
        </router-link>
  
      </nav>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  
  const auth = useAuthStore()
  const isWorker = computed(() => auth.user?.role === 'worker')
  </script>