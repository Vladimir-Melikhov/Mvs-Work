<template>
  <div class="animate-fade-in pb-20 pt-4 px-2 md:px-0">
    <div class="glass p-6 md:p-8 rounded-[40px] relative overflow-hidden mb-8 group">
      <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-[#7000ff]/10 to-[#00c6ff]/10 blur-2xl opacity-60"></div>
      
      <button @click="toggleEdit" class="absolute top-6 md:top-8 right-6 md:right-8 z-10 text-gray-400 hover:text-[#1a1a2e] text-sm font-bold transition-colors">
        {{ isEditing ? 'Отмена' : 'Редактировать' }}
      </button>

      <div class="relative flex flex-col items-center gap-6 md:flex-row md:gap-8 mt-4">
        <div class="relative w-40 h-40 md:w-48 md:h-48 shrink-0 mx-auto md:mx-0">
          <div class="w-full h-full rounded-[32px] p-1.5 shadow-2xl border border-white/30 overflow-hidden bg-white/10 backdrop-blur-md">
            <img 
              v-if="avatarPreview || user?.profile?.avatar_url" 
              :src="avatarPreview || user.profile.avatar_url" 
              class="w-full h-full rounded-[28px] object-cover"
              alt="Avatar"
            >
            <div 
              v-else 
              class="w-full h-full rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-3xl md:text-4xl font-bold"
            >
              {{ userInitials }}
            </div>
          </div>
          
          <div v-if="isEditing" class="absolute -bottom-2 left-1/2 -translate-x-1/2">
            <label class="cursor-pointer">
              <div class="bg-[#7000ff] hover:bg-[#5500cc] text-white px-3 py-1.5 rounded-full text-xs font-bold shadow-lg transition-all flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Загрузить
              </div>
              <input 
                type="file" 
                accept="image/jpeg,image/png,image/gif,image/webp"
                @change="handleAvatarUpload"
                class="hidden"
              >
            </label>
          </div>
        </div>

        <div class="text-center md:text-left flex-1 space-y-1 min-w-0 w-full">
          <div v-if="isEditing" class="flex flex-col items-center md:items-start gap-3 w-full">
             <div class="flex gap-4 mb-2" v-if="!isWorker">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500 cursor-pointer hover:text-[#1a1a2e]">
                  <input type="radio" :value="false" v-model="isCompanyEdit" class="hidden"> Человек
                </label>
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500 cursor-pointer hover:text-[#1a1a2e]">
                  <input type="radio" :value="true" v-model="isCompanyEdit" class="hidden"> Компания
                </label>
             </div>

             <input 
               v-if="isCompanyEdit && !isWorker" 
               v-model="editForm.company_name" 
               class="text-2xl md:text-4xl font-bold text-[#1a1a2e] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all"
               placeholder="Название компании"
             >
             <input 
               v-else 
               v-model="editForm.full_name" 
               class="text-2xl md:text-4xl font-bold text-[#1a1a2e] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all"
               placeholder="Ваше имя"
             >
             
             <input 
               v-if="isWorker" 
               v-model="editForm.headline" 
               placeholder="Профессия / Заголовок" 
               class="text-sm text-[#7000ff] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all font-medium"
             >
             <input 
               v-else-if="isCompanyEdit" 
               v-model="editForm.company_website" 
               placeholder="Ссылка на сайт" 
               class="text-sm text-[#7000ff] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all font-medium"
             >
             
             <!-- ✅ НОВОЕ: Редактирование социальных сетей -->
             <div class="w-full space-y-2 mt-4">
               <input 
                 v-model="editForm.github_link" 
                 placeholder="Ссылка на GitHub (https://github.com/...)" 
                 class="text-sm text-gray-600 bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all"
               >
               <input 
                 v-model="editForm.behance_link" 
                 placeholder="Ссылка на Behance (https://behance.net/...)" 
                 class="text-sm text-gray-600 bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all"
               >
             </div>
          </div>

          <div v-else class="w-full">
            <div class="inline-block px-3 py-1 rounded-full bg-white/20 border border-white/20 text-[#1a1a2e] text-[10px] font-bold uppercase tracking-wider mb-3 backdrop-blur-sm">
              {{ isWorker ? (user?.profile?.headline || 'Фрилансер') : 'Заказчик' }}
            </div>
            
            <h1 class="text-2xl md:text-4xl font-bold text-[#1a1a2e] tracking-tight break-words">
              {{ user?.profile?.company_name || user?.profile?.full_name || user?.email }}
            </h1>
            
            <div v-if="isWorker && workerRating > 0" class="flex items-center gap-3 mt-3 justify-center md:justify-start flex-wrap">
              <div class="flex gap-1">
                <div v-for="i in 5" :key="i" class="relative w-4 h-4">
                  <svg class="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <linearGradient :id="'grad-' + i">
                        <stop offset="0%" stop-color="#7000ff" />
                        <stop 
                          :offset="(Math.min(Math.max(workerRating - (i - 1), 0), 1) * 100) + '%'" 
                          stop-color="#7000ff" 
                        />
                        <stop 
                          :offset="(Math.min(Math.max(workerRating - (i - 1), 0), 1) * 100) + '%'" 
                          stop-color="#e5e7eb" 
                        />
                        <stop offset="100%" stop-color="#e5e7eb" />
                      </linearGradient>
                    </defs>
                    <path 
                      d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
                      :fill="'url(#grad-' + i + ')'"
                    />
                  </svg>
                </div>
              </div>
              
              <div class="text-xs font-bold text-gray-500 flex items-center gap-1">
                <span class="text-[#1a1a2e] text-sm">{{ workerRating.toFixed(1) }}</span>
                <span class="w-1 h-1 rounded-full bg-gray-300"></span>
                <span>{{ totalReviews }} отзывов</span>
              </div>
            </div>
            
            <!-- ✅ НОВОЕ: Отображение социальных сетей -->
            <div class="flex items-center gap-3 mt-3 justify-center md:justify-start flex-wrap">
              <a 
                v-if="user?.profile?.company_website" 
                :href="user.profile.company_website" 
                target="_blank" 
                class="text-sm text-gray-500 hover:text-[#7000ff] transition-colors break-all flex items-center gap-1"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                {{ user.profile.company_website.replace('https://', '').replace('http://', '') }}
              </a>
              
              <a 
                v-if="user?.profile?.github_link" 
                :href="user.profile.github_link" 
                target="_blank"
                rel="noopener noreferrer"
                class="w-8 h-8 rounded-full bg-gray-800 hover:bg-[#7000ff] text-white flex items-center justify-center transition-all hover:scale-110"
                title="GitHub"
              >
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
              
              <a 
                v-if="user?.profile?.behance_link" 
                :href="user.profile.behance_link" 
                target="_blank"
                rel="noopener noreferrer"
                class="w-8 h-8 rounded-full bg-[#1769ff] hover:bg-[#7000ff] text-white flex items-center justify-center transition-all hover:scale-110"
                title="Behance"
              >
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-5.101 3-3.074 0-5.564-1.729-5.564-5.675 0-3.91 2.325-5.92 5.466-5.92 3.082 0 4.964 1.782 5.375 4.426.078.506.109 1.188.095 2.14h-8.027c.13 3.211 3.483 3.312 4.588 2.029h3.168zm-7.686-4h4.965c-.105-1.547-1.136-2.219-2.477-2.219-1.466 0-2.277.768-2.488 2.219zm-9.574 6.988h-6.466v-14.967h6.953c5.476.081 5.58 5.444 2.72 6.906 3.461 1.26 3.577 8.061-3.207 8.061zm-3.466-8.988h3.584c2.508 0 2.906-3-.312-3h-3.272v3zm3.391 3h-3.391v3.016h3.341c3.055 0 2.868-3.016.05-3.016z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="isEditing" class="mt-8 flex justify-end animate-fade-in">
         <button @click="saveProfile" :disabled="uploadingAvatar" class="bg-[#1a1a2e] text-white px-6 md:px-8 py-3 rounded-2xl font-bold shadow-lg shadow-[#1a1a2e]/10 hover:scale-105 transition-transform border border-white/10 disabled:opacity-50">
            {{ uploadingAvatar ? 'Загрузка...' : 'Сохранить' }}
         </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
      <div class="glass p-6 md:p-8 rounded-[32px]">
        <h3 class="text-lg font-bold text-[#1a1a2e] mb-4 flex items-center gap-2">О себе</h3>
        <textarea 
          v-if="isEditing" 
          v-model="editForm.bio" 
          rows="5" 
          class="w-full p-4 bg-white/20 rounded-2xl border border-white/20 outline-none focus:bg-white/30 resize-none text-sm transition-all shadow-inner"
          placeholder="Расскажите о себе..."
        ></textarea>
        <p v-else class="text-gray-600 leading-relaxed whitespace-pre-wrap break-words">{{ user?.profile?.bio || 'Информация не заполнена.' }}</p>
      </div>

      <div v-if="isWorker" class="glass p-6 md:p-8 rounded-[32px]">
        <h3 class="text-lg font-bold text-[#1a1a2e] mb-4">Навыки</h3>
        
        <div v-if="isEditing" class="space-y-4">
           <div class="flex flex-wrap gap-2">
              <span v-for="(skill, idx) in editForm.skills" :key="idx" class="px-3 py-1.5 rounded-xl bg-white/30 border border-white/30 flex items-center gap-2 text-sm font-medium text-[#1a1a2e] break-words">
                {{ skill }} <button @click="editForm.skills.splice(idx,1)" class="text-red-500/70 hover:text-red-500 font-bold">×</button>
              </span>
           </div>
           <input 
              v-model="tempSkill" 
              @keydown.enter.prevent="addSkill" 
              placeholder="+ Добавить навык" 
              class="w-full p-4 bg-white/20 rounded-2xl border border-white/20 outline-none text-sm focus:bg-white/30 transition-all shadow-inner placeholder-gray-500"
            >
        </div>

        <div v-else class="flex flex-wrap gap-2">
          <span v-for="skill in user?.profile?.skills" :key="skill" class="px-3 md:px-4 py-2 rounded-xl bg-white/30 border border-white/40 text-[#1a1a2e] text-sm font-semibold shadow-sm backdrop-blur-sm break-words">
            {{ skill }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="isWorker" class="mt-8 animate-fade-in">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 px-2 gap-3">
         <h3 class="text-xl font-bold text-[#1a1a2e]">Активные услуги</h3>
         <router-link to="/create-service" class="text-xs font-bold text-[#7000ff] hover:underline bg-white/20 px-3 py-1.5 rounded-full border border-white/20 whitespace-nowrap">
           + Создать новую
         </router-link>
      </div>

      <div v-if="loadingServices" class="text-center py-10 opacity-50">
        Загрузка...
      </div>

      <div v-else-if="paginatedServices.length > 0">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          <div 
            v-for="service in paginatedServices" 
            :key="service.id" 
            class="glass rounded-[32px] p-4 md:p-6 cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1 transition-all"
            @click="$router.push(`/services/${service.id}`)" 
          >
            <div class="flex items-center gap-3 mb-4">
               <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-[10px] font-bold border border-white/30 overflow-hidden shrink-0">
                 <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
                 <span v-else>Я</span>
               </div>
               <div class="flex-1 min-w-0">
                  <div class="text-xs font-bold text-gray-400 uppercase">Моя услуга</div>
               </div>
               <div class="text-[#7000ff] font-bold text-base md:text-lg">{{ service.price }}₽</div>
            </div>

            <h3 class="text-base md:text-lg font-bold text-[#1a1a2e] mb-2 leading-tight line-clamp-2 break-words">
              {{ service.title }}
            </h3>
            <p class="text-gray-600 text-xs leading-relaxed mb-4 line-clamp-3 flex-1 break-words">
              {{ service.description }}
            </p>

            <div class="flex flex-wrap gap-2 mt-auto pt-4 border-t border-white/10">
               <span v-for="tag in service.tags?.slice(0,2)" :key="tag" class="px-2 py-1 rounded-lg bg-white/20 text-[10px] font-bold text-gray-600 border border-white/20 break-words">
                 #{{ tag }}
               </span>
            </div>
          </div>
        </div>

        <div v-if="totalServicePages > 1" class="flex justify-center items-center gap-2 mt-6">
          <button 
            @click="currentServicePage--" 
            :disabled="currentServicePage === 1"
            class="w-9 h-9 rounded-full bg-white/20 hover:bg-white/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div class="flex gap-1">
            <button 
              v-for="page in visibleServicePages" 
              :key="page"
              @click="currentServicePage = page"
              class="w-9 h-9 rounded-full font-bold text-sm transition-all"
              :class="currentServicePage === page 
                ? 'bg-[#7000ff] text-white' 
                : 'bg-white/20 hover:bg-white/40 text-gray-700'"
            >
              {{ page }}
            </button>
          </div>

          <button 
            @click="currentServicePage++" 
            :disabled="currentServicePage === totalServicePages"
            class="w-9 h-9 rounded-full bg-white/20 hover:bg-white/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <div v-else class="glass p-8 rounded-[32px] text-center border border-white/20 opacity-70">
        <p class="font-bold text-[#1a1a2e] mb-2">Услуг пока нет</p>
        <router-link to="/create-service" class="text-sm text-[#7000ff] hover:underline">Начать продавать свои навыки &rarr;</router-link>
      </div>
    </div>

    <div class="mt-8 animate-fade-in">
      <DealsHistory />
    </div>

    <div v-if="isWorker" class="mt-8 animate-fade-in">
      <ReviewsSection :worker-id="String(user.id)" @reviews-loaded="onReviewsLoaded" />
    </div>

    <button 
      @click="handleLogout" 
      class="mt-12 mx-auto block text-gray-400 hover:text-red-500 text-sm font-bold transition-colors opacity-60 hover:opacity-100"
    >
      Выйти
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'
import axios from 'axios'
import DealsHistory from '../components/DealsHistory.vue'
import ReviewsSection from '../components/ReviewsSection.vue'

const router = useRouter()
const auth = useAuthStore()
const user = computed(() => auth.user)
const isWorker = computed(() => user.value?.role === 'worker')

const isEditing = ref(false)
const isCompanyEdit = ref(false)
const tempSkill = ref('')
const editForm = ref({})

const avatarFile = ref(null)
const avatarPreview = ref(null)
const uploadingAvatar = ref(false)

const myServices = ref([])
const loadingServices = ref(false)
const currentServicePage = ref(1)
const servicesPerPage = 3

const workerRating = ref(0)
const totalReviews = ref(0)

const userInitials = computed(() => user.value?.email?.substring(0, 2).toUpperCase() || 'ME')

const totalServicePages = computed(() => Math.ceil(myServices.value.length / servicesPerPage))

const paginatedServices = computed(() => {
  const start = (currentServicePage.value - 1) * servicesPerPage
  const end = start + servicesPerPage
  return myServices.value.slice(start, end)
})

const visibleServicePages = computed(() => {
  const pages = []
  const total = totalServicePages.value
  const current = currentServicePage.value
  
  if (total <= 5) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 3) {
      pages.push(1, 2, 3, 4, 5)
    } else if (current >= total - 2) {
      pages.push(total - 4, total - 3, total - 2, total - 1, total)
    } else {
      pages.push(current - 2, current - 1, current, current + 1, current + 2)
    }
  }
  
  return pages
})

const handleAvatarUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (file.size > 5 * 1024 * 1024) {
    alert('Файл слишком большой. Максимум 5MB')
    return
  }
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('Неподдерживаемый формат. Используйте JPG, PNG, GIF или WebP')
    return
  }
  
  avatarFile.value = file
  
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)
}

const toggleEdit = () => {
  if (!isEditing.value) {
    editForm.value = JSON.parse(JSON.stringify(user.value.profile || {}))
    if (!editForm.value.skills) editForm.value.skills = []
    isCompanyEdit.value = !!editForm.value.company_name
    
    avatarFile.value = null
    avatarPreview.value = null
  }
  isEditing.value = !isEditing.value
}

const addSkill = () => {
  if (tempSkill.value.trim()) {
    editForm.value.skills.push(tempSkill.value.trim())
    tempSkill.value = ''
  }
}

const saveProfile = async () => {
  uploadingAvatar.value = true
  
  try {
    if (isCompanyEdit.value && !isWorker.value) {
      editForm.value.full_name = null
    } else {
      editForm.value.company_name = null
      if (!isWorker.value) editForm.value.company_website = null
    }
    
    const formData = new FormData()
    
    Object.keys(editForm.value).forEach(key => {
      if (key === 'avatar') return
      
      const value = editForm.value[key]
      if (value !== null && value !== undefined) {
        if (key === 'skills') {
          formData.append(key, JSON.stringify(value))
        } else {
          formData.append(key, value)
        }
      }
    })
    
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
      
      isEditing.value = false
      avatarFile.value = null
      avatarPreview.value = null
    } else {
      alert('Ошибка сохранения.')
    }
  } catch (error) {
    console.error('Save error:', error)
    alert('Ошибка сохранения: ' + (error.response?.data?.error || error.message))
  } finally {
    uploadingAvatar.value = false
  }
}

const fetchMyServices = async () => {
  if (!isWorker.value) return
  loadingServices.value = true
  try {
    const res = await axios.get(`/api/market/services/?owner_id=${auth.user.id}`)
    if (res.data.status === 'success') {
       myServices.value = res.data.data
    } else if (Array.isArray(res.data)) {
       myServices.value = res.data
    }
  } catch (e) {
    console.error("Failed to fetch my services", e)
  } finally {
    loadingServices.value = false
  }
}

const onReviewsLoaded = (data) => {
  workerRating.value = Number(data.averageRating) || 0
  totalReviews.value = Number(data.totalReviews) || 0
}

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

onMounted(async () => { 
  await auth.fetchProfile() 
  fetchMyServices()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07), 0 8px 10px -6px rgba(0, 0, 0, 0.07);
}
</style>
