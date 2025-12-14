<template>
    <div class="min-h-screen bg-[#f2f4f8] flex items-center justify-center p-4">
      <div class="glass w-full max-w-3xl rounded-[32px] overflow-hidden flex flex-col md:flex-row shadow-2xl animate-fade-in relative border border-white/60">
        
        <div class="bg-[#1a1a2e] w-full md:w-5/12 p-8 flex flex-col justify-between text-white relative">
          <div class="relative z-10 mt-4">
            <div class="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center mb-6 text-2xl">👋</div>
            <h2 class="text-3xl font-bold mb-3 leading-tight">Almost<br>There!</h2>
            <p class="text-white/60 text-sm leading-relaxed">Tell us about yourself so we can tailor the experience for you.</p>
          </div>
          
          <div class="absolute top-0 right-0 w-64 h-64 bg-[#7000ff] rounded-full blur-[80px] opacity-30 translate-x-1/3 -translate-y-1/3"></div>
          <div class="absolute bottom-0 left-0 w-48 h-48 bg-[#00c6ff] rounded-full blur-[60px] opacity-20 -translate-x-1/3 translate-y-1/3"></div>
        </div>
  
        <div class="flex-1 p-8 md:p-10 bg-white/60 backdrop-blur-md">
          <div class="space-y-6">
            
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 rounded-full bg-white shadow-md border border-gray-100 flex items-center justify-center overflow-hidden relative group">
                 <img v-if="form.avatar" :src="form.avatar" class="w-full h-full object-cover">
                 <span v-else class="text-2xl opacity-30">📷</span>
                 <input v-model="form.avatar" class="absolute inset-0 opacity-0 cursor-pointer" title="Paste Image URL">
              </div>
              <div>
                 <div class="text-xs text-gray-400 font-bold uppercase mb-1">Avatar</div>
                 <div class="text-xs text-[#7000ff]">Click to paste URL (optional)</div>
              </div>
            </div>
  
            <div v-if="!isWorker" class="bg-white/80 p-1 rounded-xl flex shadow-sm border border-gray-100">
               <button @click="isCompany = false" class="flex-1 py-2 rounded-lg text-xs font-bold transition-all" :class="!isCompany ? 'bg-[#1a1a2e] text-white shadow-md' : 'text-gray-500 hover:bg-gray-100'">Personal</button>
               <button @click="isCompany = true" class="flex-1 py-2 rounded-lg text-xs font-bold transition-all" :class="isCompany ? 'bg-[#1a1a2e] text-white shadow-md' : 'text-gray-500 hover:bg-gray-100'">Company</button>
            </div>
  
            <div class="space-y-4">
              <div>
                <label class="block text-xs font-bold text-gray-400 uppercase mb-1">
                  {{ isWorker ? 'Your Name' : (isCompany ? 'Company Name' : 'Full Name') }} <span class="text-[#7000ff]">*</span>
                </label>
                <input 
                  v-model="nameInput" 
                  class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 transition-all font-medium text-[#1a1a2e]"
                  :placeholder="isWorker ? 'John Doe' : (isCompany ? 'Acme Inc.' : 'Alex Smith')"
                >
              </div>
  
              <div>
                <label class="block text-xs font-bold text-gray-400 uppercase mb-1">About You <span class="text-[#7000ff]">*</span></label>
                <textarea 
                  v-model="form.bio" 
                  rows="3" 
                  class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm resize-none"
                  placeholder="Briefly describe your skills or what you are looking for..."
                ></textarea>
              </div>
  
              <div v-if="isWorker" class="animate-fade-in">
                 <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Professional Headline</label>
                 <input v-model="form.headline" class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm" placeholder="e.g. Senior Python Developer">
              </div>
  
              <div v-if="!isWorker && isCompany" class="animate-fade-in">
                 <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Website</label>
                 <input v-model="form.company_website" class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm" placeholder="https://mycompany.com">
              </div>
  
              <div v-if="isWorker">
                <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Skills <span class="text-[#7000ff]">*</span></label>
                <div class="bg-white/80 p-2 rounded-xl border border-gray-200 focus-within:border-[#7000ff] focus-within:ring-2 focus-within:ring-[#7000ff]/10 flex flex-wrap gap-2">
                  <span v-for="(skill, idx) in form.skills" :key="idx" class="bg-[#1a1a2e] text-white px-2 py-1 rounded text-xs font-bold flex items-center gap-1">
                    {{ skill }} <button @click="removeSkill(idx)" class="hover:text-red-300">×</button>
                  </span>
                  <input 
                    v-model="newSkill" 
                    @keydown.enter.prevent="addSkill" 
                    placeholder="Type & Enter..." 
                    class="bg-transparent outline-none text-sm py-1 px-1 flex-1 min-w-[60px]"
                  >
                </div>
              </div>
            </div>
  
            <p v-if="error" class="text-red-500 text-xs font-bold text-center bg-red-50 p-2 rounded-lg">{{ error }}</p>
  
            <button 
              @click="save" 
              :disabled="loading"
              class="w-full bg-gradient-to-r from-[#7000ff] to-[#00c6ff] text-white py-3 rounded-xl font-bold shadow-lg shadow-[#7000ff]/30 hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-70 disabled:cursor-not-allowed mt-4"
            >
              {{ loading ? 'Saving...' : 'Complete Profile →' }}
            </button>
  
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  import { useRouter } from 'vue-router'
  
  const auth = useAuthStore()
  const router = useRouter()
  const isWorker = computed(() => auth.user?.role === 'worker')
  
  const isCompany = ref(false)
  const nameInput = ref('') 
  
  const form = ref({
    bio: '', 
    avatar: '',
    headline: '',
    skills: [],
    company_website: ''
  })
  
  const newSkill = ref('')
  const error = ref('')
  const loading = ref(false)
  
  const addSkill = () => {
    const val = newSkill.value.trim()
    if (val && !form.value.skills.includes(val)) {
      form.value.skills.push(val)
      newSkill.value = ''
      error.value = ''
    }
  }
  
  const removeSkill = (idx) => {
    form.value.skills.splice(idx, 1)
  }
  
  const save = async () => {
    error.value = ''
    
    // ВАЛИДАЦИЯ
    if (!nameInput.value.trim()) {
      error.value = "Name is required."
      return
    }
  
    // Описание обязательно для всех
    if (!form.value.bio.trim()) {
      error.value = "Please write a short bio about yourself."
      return
    }
  
    // Скиллы обязательны для воркера
    if (isWorker.value && form.value.skills.length === 0) {
      error.value = "Add at least one skill."
      return
    }
  
    loading.value = true
    
    const dataToSend = { ...form.value }
    
    if (isWorker.value) {
        dataToSend.full_name = nameInput.value
        dataToSend.company_name = null
    } else {
        if (isCompany.value) {
            dataToSend.company_name = nameInput.value
            dataToSend.full_name = null
        } else {
            dataToSend.full_name = nameInput.value
            dataToSend.company_name = null
        }
    }
    
    if (!dataToSend.avatar) delete dataToSend.avatar
    
    const res = await auth.updateProfile(dataToSend)
    
    if (res.success) {
      router.push('/')
    } else {
      error.value = "Error: " + (res.error || 'Server error')
    }
    loading.value = false
  }
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(30px);
  }
  </style>