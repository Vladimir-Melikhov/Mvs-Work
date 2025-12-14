<template>
    <div class="min-h-[80vh] flex items-center justify-center">
      <div class="glass p-8 rounded-3xl w-full max-w-md border border-white/80 animate-fade-in">
        <h1 class="text-2xl font-bold text-center mb-6">Welcome Back</h1>
        <input v-model="email" type="email" placeholder="Email" class="w-full p-4 rounded-xl mb-4 bg-white/50 border border-gray-100 outline-none focus:ring-2 focus:ring-[#7000ff]/20">
        <input v-model="password" type="password" placeholder="Password" class="w-full p-4 rounded-xl mb-6 bg-white/50 border border-gray-100 outline-none focus:ring-2 focus:ring-[#7000ff]/20">
        
        <button @click="handleLogin" class="w-full bg-[#7000ff] text-white py-4 rounded-xl font-bold shadow-lg shadow-[#7000ff]/30 mb-4 hover:scale-[1.02] transition-transform">
          Login
        </button>
  
        <p class="text-center text-gray-500 text-sm">
          Don't have an account? 
          <router-link to="/register" class="text-[#7000ff] font-bold hover:underline">Register</router-link>
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
  const auth = useAuthStore()
  const router = useRouter()
  
  const handleLogin = async () => {
    const res = await auth.login(email.value, password.value)
    if (res.success) router.push('/')
    else alert('Login failed')
  }
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(15px);
  }
  </style>