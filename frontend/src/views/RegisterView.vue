<template>
    <div class="min-h-[85vh] flex items-center justify-center pt-16">
      <div class="glass p-8 rounded-[32px] w-full max-w-[420px] border border-white/60 shadow-xl animate-fade-in">
        <h1 class="text-3xl font-bold text-center mb-2 text-[#1a1a2e]">Join FreelanceHub</h1>
        <p class="text-center text-gray-400 mb-8 text-sm">Start your journey today</p>
        
        <div class="bg-gray-100/80 p-1.5 rounded-2xl mb-6 flex relative">
          <div 
            class="absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] bg-white rounded-xl shadow-sm transition-all duration-300"
            :class="role === 'client' ? 'left-1.5' : 'left-[calc(50%+3px)]'"
          ></div>
          <button 
            @click="role = 'client'" 
            class="flex-1 py-3 text-sm font-bold relative z-10 transition-colors"
            :class="role === 'client' ? 'text-[#1a1a2e]' : 'text-gray-400 hover:text-gray-600'"
          >
            I want to Hire
          </button>
          <button 
            @click="role = 'worker'" 
            class="flex-1 py-3 text-sm font-bold relative z-10 transition-colors"
            :class="role === 'worker' ? 'text-[#7000ff]' : 'text-gray-400 hover:text-gray-600'"
          >
            I want to Work
          </button>
        </div>
  
        <div class="space-y-4">
          <input 
            v-model="email" 
            type="email" 
            placeholder="Email address" 
            class="w-full p-4 rounded-xl bg-white/50 border border-gray-200 outline-none focus:ring-2 focus:ring-[#7000ff]/20 transition-all placeholder:text-gray-400 text-[#1a1a2e]"
          >
          
          <input 
            v-model="password" 
            type="password" 
            placeholder="Password (min 6 chars)" 
            class="w-full p-4 rounded-xl bg-white/50 border border-gray-200 outline-none focus:ring-2 focus:ring-[#7000ff]/20 transition-all placeholder:text-gray-400 text-[#1a1a2e]"
          >
  
          <input 
            v-model="confirmPassword" 
            type="password" 
            placeholder="Confirm Password" 
            class="w-full p-4 rounded-xl bg-white/50 border border-gray-200 outline-none focus:ring-2 focus:ring-[#7000ff]/20 transition-all placeholder:text-gray-400 text-[#1a1a2e]"
            :class="{'border-red-300 bg-red-50': password && confirmPassword && password !== confirmPassword}"
          >
        </div>
  
        <div v-if="errorMessage" class="mt-4 p-3 rounded-xl bg-red-50 text-red-500 text-xs font-bold text-center border border-red-100 animate-fade-in">
          {{ errorMessage }}
        </div>
        
        <button 
          @click="handleRegister" 
          :disabled="isLoading"
          class="w-full mt-8 bg-[#1a1a2e] text-white py-4 rounded-xl font-bold shadow-lg shadow-[#1a1a2e]/20 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {{ isLoading ? 'Creating Account...' : 'Create Account' }}
        </button>
  
        <p class="text-center text-gray-500 text-sm mt-6">
          Already have an account? 
          <router-link to="/login" class="text-[#7000ff] font-bold hover:underline">Log in</router-link>
        </p>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  import { useRouter } from 'vue-router'
  
  const email = ref('')
  const password = ref('')
  const confirmPassword = ref('') // НОВОЕ
  const role = ref('client')
  const errorMessage = ref('')
  const isLoading = ref(false)
  
  const auth = useAuthStore()
  const router = useRouter()
  
  const handleRegister = async () => {
    // Валидация
    if (!email.value || password.value.length < 6) {
      errorMessage.value = "Please enter a valid email and password (min 6 chars)"
      return
    }
  
    // Проверка совпадения паролей
    if (password.value !== confirmPassword.value) {
      errorMessage.value = "Passwords do not match!"
      return
    }
  
    isLoading.value = true
    errorMessage.value = ''
  
    const res = await auth.register(email.value, password.value, role.value)
    
    if (res.success) {
      router.push('/onboarding')
    } else {
      const err = res.error
      errorMessage.value = typeof err === 'object' ? Object.values(err).flat().join(', ') : err
    }
    
    isLoading.value = false
  }
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(20px);
  }
  </style>