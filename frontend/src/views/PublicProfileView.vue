<template>
  <div class="animate-fade-in pb-20 pt-4 px-2 md:px-0">
    <button @click="$router.back()" class="mb-4 md:mb-6 flex items-center gap-2 text-gray-500 hover:text-[#7000ff] transition-colors font-medium ml-2 md:ml-4 text-sm md:text-base">
      ← Назад
    </button>

    <div v-if="loading" class="text-center py-20">
      <div class="inline-block w-10 h-10 md:w-12 md:h-12 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
      <p class="mt-4 text-gray-500 text-sm md:text-base">Загрузка профиля...</p>
    </div>

    <div v-else-if="error" class="glass p-8 md:p-12 rounded-[32px] md:rounded-[40px] text-center border border-white/20">
      <div class="text-5xl md:text-6xl mb-4 opacity-50">😞</div>
      <h3 class="text-lg md:text-xl font-bold text-[#1a1a2e] mb-2">{{ error }}</h3>
      <button @click="$router.back()" class="mt-6 text-[#7000ff] hover:underline font-bold text-sm md:text-base">
        Вернуться назад
      </button>
    </div>

    <div v-else-if="userData">
      <!-- Шапка профиля -->
      <div class="glass p-4 md:p-8 rounded-[32px] md:rounded-[40px] relative overflow-hidden mb-6 md:mb-8">
        <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-[#7000ff]/10 to-[#00c6ff]/10 blur-2xl opacity-60"></div>

        <div class="relative flex flex-col items-center gap-4 md:gap-8 mt-4 md:flex-row">
          <!-- Аватар -->
          <div class="relative w-32 h-32 md:w-40 md:h-40 lg:w-48 lg:h-48 shrink-0 mx-auto md:mx-0">
            <div class="w-full h-full rounded-[28px] md:rounded-[32px] p-1.5 shadow-2xl border border-white/30 overflow-hidden bg-white/10 backdrop-blur-md">
              <img 
                v-if="userData.profile.avatar_url" 
                :src="userData.profile.avatar_url" 
                class="w-full h-full rounded-[24px] md:rounded-[28px] object-cover"
                alt="Avatar"
              >
              <div 
                v-else 
                class="w-full h-full rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-2xl md:text-3xl lg:text-4xl font-bold"
              >
                {{ userInitials }}
              </div>
            </div>
          </div>

          <!-- Информация -->
          <div class="text-center md:text-left flex-1 space-y-1 min-w-0 w-full">
            <div class="inline-block px-2 md:px-3 py-0.5 md:py-1 rounded-full bg-white/20 border border-white/20 text-[#1a1a2e] text-[9px] md:text-[10px] font-bold uppercase tracking-wider mb-2 md:mb-3 backdrop-blur-sm">
              {{ isWorker ? (userData.profile.headline || 'Фрилансер') : 'Заказчик' }}
            </div>
            
            <h1 class="text-xl md:text-2xl lg:text-4xl font-bold text-[#1a1a2e] tracking-tight break-words">
              {{ displayName }}
            </h1>
            
            <!-- Рейтинг для фрилансера -->
            <div v-if="isWorker && workerRating > 0" class="flex items-center gap-2 md:gap-3 mt-2 md:mt-3 justify-center md:justify-start flex-wrap">
              <div class="flex gap-1">
                <div v-for="i in 5" :key="i" class="relative w-3 h-3 md:w-4 md:h-4">
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
              
              <div class="text-[10px] md:text-xs font-bold text-gray-500 flex items-center gap-1">
                <span class="text-[#1a1a2e] text-xs md:text-sm">{{ workerRating.toFixed(1) }}</span>
                <span class="w-1 h-1 rounded-full bg-gray-300"></span>
                <span>{{ totalReviews }} отзывов</span>
              </div>
            </div>
            
            <!-- Ссылки -->
            <div class="flex items-center gap-2 md:gap-3 mt-2 md:mt-3 justify-center md:justify-start flex-wrap">
              <a 
                v-if="userData.profile.company_website" 
                :href="userData.profile.company_website" 
                target="_blank" 
                class="text-xs md:text-sm text-gray-500 hover:text-[#7000ff] transition-colors break-all flex items-center gap-1"
              >
                <svg class="w-3 h-3 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                {{ userData.profile.company_website.replace('https://', '').replace('http://', '') }}
              </a>
              
              <a 
                v-if="userData.profile.github_link" 
                :href="userData.profile.github_link" 
                target="_blank"
                rel="noopener noreferrer"
                class="w-7 h-7 md:w-8 md:h-8 rounded-full bg-gray-800 hover:bg-[#7000ff] text-white flex items-center justify-center transition-all hover:scale-110"
                title="GitHub"
              >
                <svg class="w-3 h-3 md:w-4 md:h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
              
              <a 
                v-if="userData.profile.behance_link" 
                :href="userData.profile.behance_link" 
                target="_blank"
                rel="noopener noreferrer"
                class="w-7 h-7 md:w-8 md:h-8 rounded-full bg-[#1769ff] hover:bg-[#7000ff] text-white flex items-center justify-center transition-all hover:scale-110"
                title="Behance"
              >
                <svg class="w-3 h-3 md:w-4 md:h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-5.101 3-3.074 0-5.564-1.729-5.564-5.675 0-3.91 2.325-5.92 5.466-5.92 3.082 0 4.964 1.782 5.375 4.426.078.506.109 1.188.095 2.14h-8.027c.13 3.211 3.483 3.312 4.588 2.029h3.168zm-7.686-4h4.965c-.105-1.547-1.136-2.219-2.477-2.219-1.466 0-2.277.768-2.488 2.219zm-9.574 6.988h-6.466v-14.967h6.953c5.476.081 5.58 5.444 2.72 6.906 3.461 1.26 3.577 8.061-3.207 8.061zm-3.466-8.988h3.584c2.508 0 2.906-3-.312-3h-3.272v3zm3.391 3h-3.391v3.016h3.341c3.055 0 2.868-3.016.05-3.016z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- О себе и навыки -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-6 md:mb-8">
        <div class="glass p-4 md:p-6 lg:p-8 rounded-[24px] md:rounded-[32px]">
          <h3 class="text-base md:text-lg font-bold text-[#1a1a2e] mb-3 md:mb-4 flex items-center gap-2">О себе</h3>
          <p class="text-gray-600 leading-relaxed whitespace-pre-wrap break-words text-xs md:text-sm lg:text-base">
            {{ userData.profile.bio || 'Информация не заполнена.' }}
          </p>
        </div>

        <div v-if="isWorker" class="glass p-4 md:p-6 lg:p-8 rounded-[24px] md:rounded-[32px]">
          <h3 class="text-base md:text-lg font-bold text-[#1a1a2e] mb-3 md:mb-4">Навыки</h3>
          <div v-if="userData.profile.skills && userData.profile.skills.length > 0" class="flex flex-wrap gap-1.5 md:gap-2">
            <span v-for="skill in userData.profile.skills" :key="skill" class="px-2 md:px-3 lg:px-4 py-1 md:py-1.5 lg:py-2 rounded-lg md:rounded-xl bg-white/30 border border-white/40 text-[#1a1a2e] text-xs md:text-sm font-semibold shadow-sm backdrop-blur-sm break-words">
              {{ skill }}
            </span>
          </div>
          <p v-else class="text-gray-400 text-xs md:text-sm">Навыки не указаны</p>
        </div>
      </div>

      <!-- Услуги -->
      <div v-if="isWorker" class="mt-6 md:mt-8 animate-fade-in">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 md:mb-6 px-2 gap-3">
          <h3 class="text-lg md:text-xl font-bold text-[#1a1a2e]">Услуги специалиста</h3>
        </div>

        <div v-if="loadingServices" class="text-center py-10 opacity-50">
          <div class="inline-block w-6 h-6 md:w-8 md:h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
        </div>

        <div v-else-if="services.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4 lg:gap-6">
          <div 
            v-for="service in services" 
            :key="service.id" 
            class="glass rounded-[24px] md:rounded-[32px] p-3 md:p-4 lg:p-6 cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1 transition-all"
            @click="$router.push(`/services/${service.id}`)" 
          >
            <div class="flex items-center gap-2 md:gap-3 mb-3 md:mb-4">
              <div class="w-6 h-6 md:w-8 md:h-8 rounded-full bg-white/20 flex items-center justify-center text-[9px] md:text-[10px] font-bold border border-white/30 overflow-hidden shrink-0">
                <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
                <span v-else>{{ userInitials }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-[10px] md:text-xs font-bold text-gray-400 uppercase">{{ service.category }}</div>
              </div>
              <div class="text-[#7000ff] font-bold text-sm md:text-base lg:text-lg">{{ parseInt(service.price) }}₽</div>
            </div>

            <h3 class="text-sm md:text-base lg:text-lg font-bold text-[#1a1a2e] mb-1 md:mb-2 leading-tight line-clamp-2 break-words">
              {{ service.title }}
            </h3>
            <p class="text-gray-600 text-[10px] md:text-xs leading-relaxed mb-3 md:mb-4 line-clamp-3 flex-1 break-words">
              {{ service.description }}
            </p>

            <div class="flex flex-wrap gap-1.5 md:gap-2 mt-auto pt-3 md:pt-4 border-t border-white/10">
              <span v-for="tag in service.tags?.slice(0,2)" :key="tag" class="px-1.5 md:px-2 py-0.5 md:py-1 rounded-md md:rounded-lg bg-white/20 text-[9px] md:text-[10px] font-bold text-gray-600 border border-white/20 break-words">
                #{{ tag }}
              </span>
            </div>
          </div>
        </div>

        <div v-else class="glass p-6 md:p-8 rounded-[24px] md:rounded-[32px] text-center border border-white/20 opacity-70">
          <p class="font-bold text-[#1a1a2e] mb-2 text-sm md:text-base">Услуг пока нет</p>
        </div>
      </div>

      <!-- Отзывы -->
      <div v-if="isWorker" class="mt-6 md:mt-8 animate-fade-in">
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
