<template>
    <div class="min-h-screen pt-12 pb-20 px-4 flex justify-center animate-fade-in">
      <div class="w-full max-w-2xl glass p-10 rounded-[40px] relative">
        <div class="text-center mb-10">
          <h1 class="text-3xl font-bold text-[#1a1a2e] mb-2">New Service</h1>
          <p class="text-gray-500 text-sm">Create a gig to start earning</p>
        </div>
        <div class="space-y-6">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">Title</label>
            <input v-model="form.title" placeholder="I will do..." class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 transition-all text-lg font-medium text-[#1a1a2e] shadow-inner">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">Description</label>
            <textarea v-model="form.description" rows="6" class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 resize-none text-gray-600 shadow-inner"></textarea>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">Price ($)</label>
              <input v-model="form.price" type="number" class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 font-bold text-[#7000ff] shadow-inner">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">AI Template</label>
              <input v-model="form.ai_template" class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 text-sm shadow-inner">
            </div>
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">Tags</label>
            <div class="bg-white/10 p-2 rounded-2xl border border-white/20 flex flex-wrap gap-2 min-h-[60px] shadow-inner">
              <span v-for="(tag, idx) in form.tags" :key="idx" class="bg-[#1a1a2e] text-white px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2">{{ tag }} <button @click="form.tags.splice(idx,1)">×</button></span>
              <input v-model="newTag" @keydown.enter.prevent="addTag" placeholder="Add tag..." class="bg-transparent outline-none text-sm py-1 px-2 flex-1 min-w-[100px] text-[#1a1a2e]">
            </div>
          </div>
          <p v-if="error" class="text-red-500 text-center">{{ error }}</p>
          <button @click="createService" :disabled="loading" class="w-full bg-[#1a1a2e] text-white py-4 rounded-2xl font-bold shadow-lg hover:scale-[1.01] transition-all border border-white/10">{{ loading ? 'Publishing...' : 'Publish Service' }}</button>
        </div>
      </div>
    </div>
  </template>
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '../stores/authStore'
  const router = useRouter(); const auth = useAuthStore()
  const form = ref({ title: '', description: '', price: '', ai_template: '', tags: [] })
  const newTag = ref(''); const loading = ref(false); const error = ref('')
  const addTag = () => { if(newTag.value.trim()){ form.value.tags.push(newTag.value.trim()); newTag.value='' } }
  const createService = async () => {
    if (!form.value.title || !form.value.price) return error.value = "Required fields missing"
    loading.value = true
    try {
      const payload = { ...form.value, owner_name: auth.user.profile.company_name || auth.user.profile.full_name || 'Freelancer', owner_avatar: auth.user.profile.avatar }
      await axios.post('/api/market/services/', payload)
      router.push('/profile')
    } catch (e) { error.value = "Error creating service" }
    loading.value = false
  }
  </script>
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    /* Изменено: Тень стала значительно больше и чуть темнее (0.15 вместо 0.05) */
    box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.15);
  }
  </style>