<template>
  <div class="min-h-screen bg-[#f2f4f8] flex items-center justify-center p-4">
    <div class="glass w-full max-w-3xl rounded-[32px] overflow-hidden flex flex-col md:flex-row shadow-2xl animate-fade-in relative border border-white/60">
      
      <div class="bg-[#1a1a2e] w-full md:w-5/12 p-8 flex flex-col justify-between text-white relative">
        <div class="relative z-10 mt-4">
          <div class="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center mb-6 text-2xl">👋</div>
          <h2 class="text-3xl font-bold mb-3 leading-tight">Добро<br>пожаловать!</h2>
          <p class="text-white/60 text-sm leading-relaxed">Заполните информацию о себе — это повышает шансы на получение заказа на 70%</p>
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
               <div class="text-xs text-gray-400 font-bold uppercase mb-1">Аватар</div>
               <div class="text-xs text-[#7000ff]">Нажмите что бы загрузить (JPG, PNG..)</div>
            </div>
          </div>

          <!-- ✅ НОВОЕ: Переключатель типа профиля (для всех) -->
          <div class="bg-white/80 p-1 rounded-xl flex shadow-sm border border-gray-100">
             <button @click="isCompany = false" class="flex-1 py-2 rounded-lg text-xs font-bold transition-all" :class="!isCompany ? 'bg-[#1a1a2e] text-white shadow-md' : 'text-gray-500 hover:bg-gray-100'">Personal</button>
             <button @click="isCompany = true" class="flex-1 py-2 rounded-lg text-xs font-bold transition-all" :class="isCompany ? 'bg-[#1a1a2e] text-white shadow-md' : 'text-gray-500 hover:bg-gray-100'">Company</button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">
                {{ isCompany ? 'Название компании' : 'Ваше имя' }} <span class="text-[#7000ff]">*</span>
              </label>
              <input 
                v-model="nameInput" 
                class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 transition-all font-medium text-[#1a1a2e]"
                :placeholder="isCompany ? 'Mvs Inc.' : 'Имя Фамилия'"
              >
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">О себе <span class="text-[#7000ff]">*</span></label>
              <textarea 
                v-model="form.bio" 
                rows="3" 
                class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm resize-none"
                placeholder="Информация о вас..."
              ></textarea>
            </div>

            <div v-if="isWorker" class="animate-fade-in">
               <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Профессиональное позиционирование</label>
               <input v-model="form.headline" class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm" placeholder="Video Creator & Motion Designer">
            </div>

            <div v-if="isCompany" class="animate-fade-in">
               <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Website</label>
               <input v-model="form.company_website" class="w-full p-3 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm" placeholder="https://mycompany.com">
            </div>

            <div v-if="isWorker">
              <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Навыки <span class="text-[#7000ff]">*</span></label>
              <div class="bg-white/80 p-2 rounded-xl border border-gray-200 focus-within:border-[#7000ff] focus-within:ring-2 focus-within:ring-[#7000ff]/10 flex flex-wrap gap-2">
                <span v-for="(skill, idx) in form.skills" :key="idx" class="bg-[#1a1a2e] text-white px-2 py-1 rounded text-xs font-bold flex items-center gap-1">
                  {{ skill }} <button @click="removeSkill(idx)" class="hover:text-red-300">×</button>
                </span>
                <input 
                  v-model="newSkill" 
                  @keydown.enter.prevent="addSkill" 
                  placeholder="Введите скилл & Нажмите enter..." 
                  class="bg-transparent outline-none text-sm py-1 px-1 flex-1 min-w-[60px]"
                >
              </div>
            </div>
          </div>
          <div v-if="isWorker" class="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
           <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-1">GitHub Profile</label>
          <div class="relative">
            <input 
              v-model="form.github_link" 
              class="w-full p-3 pl-10 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm" 
              placeholder="https://github.com/username"
            >
          <div class="absolute left-3 top-1/2 -translate-y-1/2 opacity-30">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          </div>
        </div>
      </div>
      <div>
        <label class="block text-xs font-bold text-gray-400 uppercase mb-1">Behance Portfolio</label>
        <div class="relative">
          <input 
            v-model="form.behance_link" 
            class="w-full p-3 pl-10 bg-white/80 rounded-xl border border-gray-200 outline-none focus:border-[#7000ff] focus:ring-2 focus:ring-[#7000ff]/10 text-sm" 
            placeholder="https://behance.net/username"
          >
        <div class="absolute left-3 top-1/2 -translate-y-1/2 opacity-30">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-5.101 3-3.074 0-5.564-1.729-5.564-5.675 0-3.91 2.325-5.92 5.466-5.92 3.082 0 4.964 1.782 5.375 4.426.078.506.109 1.188.095 2.14h-8.027c.13 3.211 3.483 3.312 4.588 2.029h3.168zm-7.686-4h4.965c-.105-1.547-1.136-2.219-2.477-2.219-1.466 0-2.277.768-2.488 2.219zm-9.574 6.988h-6.466v-14.967h6.953c5.476.081 5.58 5.444 2.72 6.906 3.461 1.26 3.577 8.061-3.207 8.061zm-3.466-8.988h3.584c2.508 0 2.906-3-.312-3h-3.272v3zm3.391 3h-3.391v3.016h3.341c3.055 0 2.868-3.016.05-3.016z"/></svg>
        </div>
      </div>
    </div>
  </div>

          <p v-if="error" class="text-red-500 text-xs font-bold text-center bg-red-50 p-2 rounded-lg">{{ error }}</p>

          <button 
            @click="save" 
            :disabled="loading"
            class="w-full bg-gradient-to-r from-[#7000ff] to-[#00c6ff] text-white py-3 rounded-xl font-bold shadow-lg shadow-[#7000ff]/30 hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-70 disabled:cursor-not-allowed mt-4"
          >
            {{ loading ? 'Сохранение...' : 'Завершить →' }}
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
  company_website: '',
  github_link: '',
  behance_link: ''
})

const avatarFile = ref(null)
const avatarPreview = ref(null)

const newSkill = ref('')
const error = ref('')
const loading = ref(false)

const handleAvatarUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Файл слишком большой. Максимум 5MB'
    return
  }
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    error.value = 'Неподдерживаемый формат. Используйте JPG, PNG, GIF или WebP'
    return
  }
  
  avatarFile.value = file
  error.value = ''
  
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
  
  if (!nameInput.value.trim()) {
    error.value = "Имя или название компании обязательно для заполнения."
    return
  }

  if (!form.value.bio.trim()) {
    error.value = "Пожалуйста, напишите немного о себе."
    return
  }

  if (isWorker.value && form.value.skills.length === 0) {
    error.value = "Добавьте хотя бы один навык."
    return
  }

  loading.value = true
  
  try {
    const formData = new FormData()
    
    if (isCompany.value) {
      formData.append('company_name', nameInput.value)
    } else {
      formData.append('full_name', nameInput.value)
    }
    
    formData.append('bio', form.value.bio)
    
    if (form.value.headline) {
      formData.append('headline', form.value.headline)
    }
    
    if (form.value.company_website) {
      formData.append('company_website', form.value.company_website)
    }

    if (form.value.github_link) {
      formData.append('github_link', form.value.github_link)
    }

    if (form.value.behance_link) {
      formData.append('behance_link', form.value.behance_link)
    }
    
    if (form.value.skills.length > 0) {
      formData.append('skills', JSON.stringify(form.value.skills))
    }
    
    if (avatarFile.value) {
      formData.append('avatar', avatarFile.value)
    }
    
    const res = await axios.patch('/api/auth/profile/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.data.status === 'success') {
      auth.user = res.data.data
      router.push('/')
    } else {
      error.value = "Ошибка: " + (res.data.error || 'Ошибка сервера')
    }
  } catch (err) {
    console.error('Save error:', err)
    error.value = "Ошибка: " + (err.response?.data?.error || err.message)
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