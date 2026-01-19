<template>
    <div class="animate-fade-in pb-20 pt-4 px-2 md:px-0">
      <button @click="$router.back()" class="mb-6 flex items-center gap-2 text-gray-500 hover:text-[#7000ff] transition-colors font-medium ml-4">
        ← Назад
      </button>
  
      <div v-if="loading" class="text-center py-20">
        <div class="inline-block w-12 h-12 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
        <p class="mt-4 text-gray-500">Загрузка профиля...</p>
      </div>
  
      <div v-else-if="error" class="glass p-12 rounded-[40px] text-center border border-white/20">
        <div class="text-6xl mb-4 opacity-50">😞</div>
        <h3 class="text-xl font-bold text-[#1a1a2e] mb-2">{{ error }}</h3>
        <button @click="$router.back()" class="mt-6 text-[#7000ff] hover:underline font-bold">
          Вернуться назад
        </button>
      </div>
  
      <div v-else-if="userData">
        <!-- Шапка профиля -->
        <div class="glass p-6 md:p-8 rounded-[40px] relative overflow-hidden mb-8">
          <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-[#7000ff]/10 to-[#00c6ff]/10 blur-2xl opacity-60"></div>
  
          <div class="relative flex flex-col items-center gap-6 md:flex-row md:gap-8 mt-4">
            <!-- Аватар -->
            <div class="w-28 md:w-32 h-28 md:h-32 shrink-0">
              <div class="w-full h-full rounded-full p-1.5 shadow-xl border border-white/20 overflow-hidden">
                <img 
                  v-if="userData.profile.avatar_url" 
                  :src="userData.profile.avatar_url" 
                  class="w-full h-full rounded-full object-cover"
                  alt="Avatar"
                >
                <div 
                  v-else 
                  class="w-full h-full rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-3xl md:text-4xl font-bold"
                >
                  {{ userInitials }}
                </div>
              </div>
            </div>
  
            <!-- Информация -->
            <div class="text-center md:text-left flex-1 space-y-1 min-w-0 w-full">
              <div class="inline-block px-3 py-1 rounded-full bg-white/20 border border-white/20 text-[#1a1a2e] text-[10px] font-bold uppercase tracking-wider mb-3 backdrop-blur-sm">
                {{ isWorker ? (userData.profile.headline || 'Фрилансер') : 'Заказчик' }}
              </div>
              
              <h1 class="text-2xl md:text-4xl font-bold text-[#1a1a2e] tracking-tight break-words">
                {{ displayName }}
              </h1>
              
              <!-- Рейтинг для фрилансера -->
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
              
              <a v-if="userData.profile.company_website" :href="userData.profile.company_website" target="_blank" class="text-sm text-gray-500 hover:text-[#7000ff] block mt-1 transition-colors break-all">
                {{ userData.profile.company_website.replace('https://', '') }}
              </a>
            </div>
          </div>
        </div>
  
        <!-- О себе и навыки -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-8">
          <div class="glass p-6 md:p-8 rounded-[32px]">
            <h3 class="text-lg font-bold text-[#1a1a2e] mb-4 flex items-center gap-2">О себе</h3>
            <p class="text-gray-600 leading-relaxed whitespace-pre-wrap break-words">
              {{ userData.profile.bio || 'Информация не заполнена.' }}
            </p>
          </div>
  
          <div v-if="isWorker" class="glass p-6 md:p-8 rounded-[32px]">
            <h3 class="text-lg font-bold text-[#1a1a2e] mb-4">Навыки</h3>
            <div v-if="userData.profile.skills && userData.profile.skills.length > 0" class="flex flex-wrap gap-2">
              <span v-for="skill in userData.profile.skills" :key="skill" class="px-3 md:px-4 py-2 rounded-xl bg-white/30 border border-white/40 text-[#1a1a2e] text-sm font-semibold shadow-sm backdrop-blur-sm break-words">
                {{ skill }}
              </span>
            </div>
            <p v-else class="text-gray-400 text-sm">Навыки не указаны</p>
          </div>
        </div>
  
        <!-- Услуги -->
        <div v-if="isWorker" class="mt-8 animate-fade-in">
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 px-2 gap-3">
            <h3 class="text-xl font-bold text-[#1a1a2e]">Услуги специалиста</h3>
          </div>
  
          <div v-if="loadingServices" class="text-center py-10 opacity-50">
            <div class="inline-block w-8 h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
          </div>
  
          <div v-else-if="services.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            <div 
              v-for="service in services" 
              :key="service.id" 
              class="glass rounded-[32px] p-4 md:p-6 cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1 transition-all"
              @click="$router.push(`/services/${service.id}`)" 
            >
              <div class="flex items-center gap-3 mb-4">
                <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-[10px] font-bold border border-white/30 overflow-hidden shrink-0">
                  <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
                  <span v-else>{{ userInitials }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-xs font-bold text-gray-400 uppercase">{{ service.category }}</div>
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
  
          <div v-else class="glass p-8 rounded-[32px] text-center border border-white/20 opacity-70">
            <p class="font-bold text-[#1a1a2e] mb-2">Услуг пока нет</p>
          </div>
        </div>
  
        <!-- Отзывы -->
        <div v-if="isWorker" class="mt-8 animate-fade-in">
          <ReviewsSection :worker-id="userId" @reviews-loaded="onReviewsLoaded" />
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import axios from 'axios'
  import ReviewsSection from '../components/ReviewsSection.vue'
  
  const route = useRoute()
  const userId = route.params.id
  
  const userData = ref(null)
  const loading = ref(true)
  const error = ref('')
  
  const services = ref([])
  const loadingServices = ref(false)
  
  const workerRating = ref(0)
  const totalReviews = ref(0)
  
  const userInitials = computed(() => {
    if (!userData.value) return '?'
    const name = userData.value.profile.company_name || userData.value.profile.full_name || userData.value.email
    return name.substring(0, 2).toUpperCase()
  })
  
  const displayName = computed(() => {
    if (!userData.value) return ''
    return userData.value.profile.company_name || userData.value.profile.full_name || userData.value.email
  })
  
  const isWorker = computed(() => userData.value?.role === 'worker')
  
  const fetchProfile = async () => {
    loading.value = true
    try {
      const res = await axios.get(`/api/auth/users/${userId}/`)
      
      if (res.data.status === 'success') {
        userData.value = res.data.data
        
        // Если фрилансер - загружаем его услуги
        if (userData.value.role === 'worker') {
          fetchServices()
        }
      } else {
        error.value = res.data.error || 'Не удалось загрузить профиль'
      }
    } catch (e) {
      console.error('Fetch profile error:', e)
      error.value = e.response?.data?.error || 'Пользователь не найден'
    } finally {
      loading.value = false
    }
  }
  
  const fetchServices = async () => {
    loadingServices.value = true
    try {
      const res = await axios.get(`/api/market/services/?owner_id=${userId}`)
      
      if (res.data.status === 'success') {
        services.value = res.data.data
      } else if (Array.isArray(res.data)) {
        services.value = res.data
      }
    } catch (e) {
      console.error("Failed to fetch services", e)
    } finally {
      loadingServices.value = false
    }
  }
  
  const onReviewsLoaded = (data) => {
    workerRating.value = Number(data.averageRating) || 0
    totalReviews.value = Number(data.totalReviews) || 0
  }
  
  onMounted(() => {
    fetchProfile()
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
  