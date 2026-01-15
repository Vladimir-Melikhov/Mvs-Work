<template>
  <div class="fixed bottom-4 left-4 right-4 z-50 flex justify-center">
    
    <nav class="w-full max-w-[400px] bg-white/10 backdrop-blur-3xl border border-white/20 rounded-full p-2 px-4 flex justify-between items-center shadow-lg shadow-black/5">
      
      <router-link 
        to="/search" 
        class="flex flex-col items-center justify-center w-14 h-14 rounded-full text-gray-500 transition-all hover:bg-white/10 hover:text-[#1a1a2e]"
        active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] backdrop-blur-md shadow-sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </router-link>
      
      <router-link 
        v-if="isWorker"
        to="/create-service"
        class="flex items-center justify-center w-14 h-14 rounded-full bg-[#1a1a2e] text-white shadow-md border border-white/10 hover:scale-105 transition-transform"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </router-link>
      
      <router-link 
        to="/chats" 
        class="flex flex-col items-center justify-center w-14 h-14 rounded-full text-gray-500 transition-all hover:bg-white/10 hover:text-[#1a1a2e]"
        active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] backdrop-blur-md shadow-sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </router-link>
      
      <router-link 
        to="/profile" 
        class="flex flex-col items-center justify-center w-14 h-14 rounded-full text-gray-500 transition-all hover:bg-white/10 hover:text-[#1a1a2e]"
        active-class="bg-gray-900/5 border border-white/30 text-[#1a1a2e] backdrop-blur-md shadow-sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
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