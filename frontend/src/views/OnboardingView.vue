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
          
          <!-- ✅ ОБНОВЛЕНО: Загрузка аватара -->
          <div class="flex items-center gap-4">
            <div class="relative w-16 h-16 rounded-full bg-white shadow-md border border-gray-100 overflow-hidden group">
              <img v-if="avatarPreview" :src="avatarPreview" class="w-full h-full object-cover">
              <span v-else class="w-full h-full flex items-center justify-center text-2xl opacity-30">📷</span>
              
              <label class="absolute inset-0 cursor-pointer bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center">
                <svg class="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <input 
                  type="file" 
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  @change="handleAvatarUpload"
                  class="hidden"
                >
              </label>
            </div>
            <div>
               <div class="text-xs text-gray-400 font-bold uppercase mb-1">Avatar</div>
               <div class="text-xs text-[#7000ff]">Click to upload (JPG, PNG, GIF)</div>
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
import axios from 'axios'

const auth = useAuthStore()
const router = useRouter()
const isWorker = computed(() => auth.user?.role === 'worker')

const isCompany = ref(false)
const nameInput = ref('') 

const form = ref({
  bio: '', 
  headline: '',
  skills: [],
  company_website: ''
})

// ✅ ДОБАВЛЕНО: Состояние для аватара
const avatarFile = ref(null)
const avatarPreview = ref(null)

const newSkill = ref('')
const error = ref('')
const loading = ref(false)

// ✅ ДОБАВЛЕНО: Обработчик загрузки аватара
const handleAvatarUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // Проверка размера
  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Файл слишком большой. Максимум 5MB'
    return
  }
  
  // Проверка типа
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    error.value = 'Неподдерживаемый формат. Используйте JPG, PNG, GIF или WebP'
    return
  }
  
  avatarFile.value = file
  error.value = ''
  
  // Создаем preview
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)
}

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

  if (!form.value.bio.trim()) {
    error.value = "Please write a short bio about yourself."
    return
  }

  if (isWorker.value && form.value.skills.length === 0) {
    error.value = "Add at least one skill."
    return
  }

  loading.value = true
  
  try {
    // Создаем FormData
    const formData = new FormData()
    
    // Добавляем текстовые поля
    if (isWorker.value) {
      formData.append('full_name', nameInput.value)
    } else {
      if (isCompany.value) {
        formData.append('company_name', nameInput.value)
      } else {
        formData.append('full_name', nameInput.value)
      }
    }
    
    formData.append('bio', form.value.bio)
    
    if (form.value.headline) {
      formData.append('headline', form.value.headline)
    }
    
    if (form.value.company_website) {
      formData.append('company_website', form.value.company_website)
    }
    
    if (form.value.skills.length > 0) {
      formData.append('skills', JSON.stringify(form.value.skills))
    }
    
    // Добавляем файл аватара, если он был выбран
    if (avatarFile.value) {
      formData.append('avatar', avatarFile.value)
    }
    
    // Отправляем запрос
    const res = await axios.patch('/api/auth/profile/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.data.status === 'success') {
      // Обновляем данные пользователя
      auth.user = res.data.data
      router.push('/')
    } else {
      error.value = "Error: " + (res.data.error || 'Server error')
    }
  } catch (err) {
    console.error('Save error:', err)
    error.value = "Error: " + (err.response?.data?.error || err.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(30px);
}
</style>
