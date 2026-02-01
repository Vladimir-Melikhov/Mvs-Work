<template>
  <div class="animate-fade-in pb-20 pt-4 md:pt-6">
    <button @click="$router.back()" class="mb-4 md:mb-6 flex items-center gap-2 text-gray-500 hover:text-[#7000ff] transition-colors font-medium ml-2 md:ml-4 text-sm md:text-base">
      ← Назад
    </button>

    <div v-if="service" class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-8 max-w-7xl mx-auto px-2 md:px-4">
      
      <div class="lg:col-span-2"> 
        <div class="glass overflow-hidden rounded-[24px] md:rounded-[40px] border border-white/20">
          
          <div v-if="service.images && service.images.length > 0" class="glass-slider overflow-hidden relative aspect-video group">
            <div 
              class="flex h-full transition-transform duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]" 
              :style="{ transform: `translateX(-${currentSlide * 100}%)` }"
              @touchstart="onTouchStart"
              @touchend="onTouchEnd"
            >
              <div v-for="img in service.images" :key="img.id" class="min-w-full h-full relative">
                <img :src="img.image_url" class="w-full h-full object-cover" alt="Service image">
              </div>
            </div>

            <div v-if="service.images.length > 1" class="absolute inset-0 flex items-center justify-between p-2 md:p-4 opacity-0 md:group-hover:opacity-100 transition-opacity pointer-events-none md:pointer-events-auto">
              <button @click.stop="prevSlide" class="w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center text-white hover:bg-white/40 transition-all pointer-events-auto">
                <svg class="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
              <button @click.stop="nextSlide" class="w-10 h-10 md:w-12 md:h-12 rounded-full bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center text-white hover:bg-white/40 transition-all pointer-events-auto">
                <svg class="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>

            <div v-if="service.images.length > 1" class="absolute bottom-3 md:bottom-6 left-1/2 -translate-x-1/2 flex gap-1.5 md:gap-2">
              <div 
                v-for="(_, index) in service.images" :key="index"
                class="h-1 md:h-1.5 rounded-full transition-all duration-300 shadow-sm"
                :class="currentSlide === index ? 'w-6 md:w-8 bg-white' : 'w-1.5 md:w-2 bg-white/40'"
              ></div>
            </div>
          </div>

          <div class="p-4 md:p-8 lg:p-12">
            <div class="flex flex-col gap-3 md:gap-4 mb-6 md:mb-8">
               <div class="flex items-start justify-between gap-3">
                 <h1 class="text-xl md:text-3xl lg:text-4xl font-black text-[#1a1a2e] leading-tight tracking-tight flex-1">
                   {{ service.title }}
                 </h1>
                 <span class="bg-[#7000ff]/10 text-[#7000ff] px-3 py-1 md:px-5 md:py-1.5 rounded-full text-[10px] md:text-xs font-black uppercase tracking-widest whitespace-nowrap shrink-0">
                   {{ service.category || 'Development' }}
                 </span>
               </div>
            </div>
            
            <div class="text-gray-900 leading-relaxed md:leading-[1.8] whitespace-pre-line mb-6 md:mb-10 text-sm md:text-lg break-words">
              {{ service.description }}
            </div>

            <div class="flex flex-wrap gap-1.5 md:gap-2 pt-6 md:pt-8 border-t border-gray-100">
              <span v-for="tag in service.tags" :key="tag" class="px-2.5 py-1 md:px-4 md:py-2 rounded-lg md:rounded-xl bg-gray-100/50 text-gray-500 text-xs md:text-sm font-bold border border-white/20 shadow-sm break-words">
                #{{ tag }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-6 md:mt-8 animate-fade-in">
          <ReviewsSection :worker-id="String(service.owner_id)" @reviews-loaded="onReviewsLoaded" />
        </div>
      </div>

      <div class="space-y-4 md:space-y-6">
        <div class="ios-glass-card p-6 md:p-8 lg:sticky lg:top-24">
          <div class="text-2xl md:text-3xl font-black text-[#7000ff] mb-1 md:mb-2 drop-shadow-sm">{{ Math.floor(service.price) }} ₽</div>
          <p class="text-gray-500 text-[10px] md:text-xs font-bold uppercase tracking-widest mb-6 md:mb-8">Начальная цена</p>
          
          <div v-if="isOwner" class="space-y-3 md:space-y-4">
             <div class="ios-inner-inset p-3 md:p-4 flex items-center gap-2 md:gap-3 mb-3 md:mb-4">
               <div class="w-7 h-7 md:w-8 md:h-8 rounded-full bg-[#1a1a2e] flex items-center justify-center text-white shrink-0">
                 <svg class="h-3.5 w-3.5 md:h-4 md:w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
               </div>
               <span class="text-[9px] md:text-[10px] font-black text-[#1a1a2e] uppercase tracking-wider">Это ваше объявление</span>
             </div>
             
             <button @click="$router.push(`/my-services/edit/${service.id}`)" class="ios-button-secondary py-3 md:py-4 w-full text-sm md:text-base">
               Редактировать
             </button>

             <button @click="deleteService" class="ios-button-danger py-3 md:py-4 w-full text-sm md:text-base">
               Удалить
             </button>
          </div>

          <div v-else>
            <button @click="showWizard = true" class="ios-button py-3.5 md:py-4 w-full text-sm md:text-base">
              Начать сделку с AI
            </button>
            
            <div class="mt-8 md:mt-10 pt-6 md:pt-8 border-t border-black/5">
              <div class="flex items-center gap-3 md:gap-4 cursor-pointer group hover:bg-black/5 -m-2 p-2 md:p-3 rounded-[20px] md:rounded-[24px] transition-all" @click="goToOwnerProfile">
                <UserAvatar :avatar-url="service.owner_avatar" :name="service.owner_name || 'Пользователь'" size="md" class="border-2 border-white shadow-sm group-hover:ring-2 group-hover:ring-[#7000ff] transition-all md:w-12 md:h-12" />
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-sm md:text-base text-[#1a1a2e] group-hover:text-[#7000ff] transition-colors truncate tracking-tight">{{ service.owner_name || 'Пользователь' }}</div>
                  <div class="text-[9px] md:text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-1.5 md:gap-2">
                    <span>Профиль автора</span>
                    <span v-if="workerRating > 0" class="text-[#7000ff] font-black">★ {{ workerRating.toFixed(1) }}</span>
                  </div>
                </div>
                <svg class="w-4 h-4 md:w-5 md:h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" stroke-width="2.5" /></svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AiDealWizard v-if="showWizard" :service="service" @close="showWizard = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import axios from 'axios'
import AiDealWizard from '../components/AiDealWizard.vue'
import UserAvatar from '../components/UserAvatar.vue'
import ReviewsSection from '../components/ReviewsSection.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const service = ref(null)
const showWizard = ref(false)
const currentSlide = ref(0)
const touchStartX = ref(0)

const workerRating = ref(0)
const totalReviews = ref(0)

const nextSlide = () => {
  if (currentSlide.value < service.value.images.length - 1) currentSlide.value++
  else currentSlide.value = 0
}
const prevSlide = () => {
  if (currentSlide.value > 0) currentSlide.value--
  else currentSlide.value = service.value.images.length - 1
}
const onTouchStart = (e) => { touchStartX.value = e.touches[0].clientX }
const onTouchEnd = (e) => {
  const diff = touchStartX.value - e.changedTouches[0].clientX
  if (Math.abs(diff) > 50) diff > 0 ? nextSlide() : prevSlide()
}

const isOwner = computed(() => service.value && auth.user && String(service.value.owner_id) === String(auth.user.id))
const goToOwnerProfile = () => service.value?.owner_id && router.push(`/users/${service.value.owner_id}`)

const onReviewsLoaded = (data) => {
  workerRating.value = Number(data.averageRating) || 0
  totalReviews.value = Number(data.totalReviews) || 0
}

const fetchService = async () => {
  try {
    const res = await axios.get(`/api/market/services/${route.params.id}/`)
    service.value = res.data.data
  } catch (e) { console.error("Failed to fetch service") }
}

const deleteService = async () => {
  if (!confirm('Вы уверены?')) return
  try {
    await axios.delete(`/api/market/services/${service.value.id}/`)
    router.push('/profile')
  } catch (e) { alert('Ошибка при удалении') }
}

onMounted(async () => {
  if (!auth.user) await auth.fetchProfile()
  fetchService()
})
</script>

<style scoped>
.ios-glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-radius: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.8);
  border-left: 1px solid rgba(255, 255, 255, 0.4);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.1), 
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .ios-glass-card {
    border-radius: 28px;
  }
}

.ios-inner-inset {
  background: rgba(0, 0, 0, 0.05); 
  border-radius: 20px;
  box-shadow: 
    inset 0 2px 4px rgba(0, 0, 0, 0.05), 
    0 1px 0 rgba(255, 255, 255, 0.5);
}

.ios-button {
  border-radius: 24px;
  font-weight: 800;
  color: white;
  background: #7000ff; 
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 
    0 10px 20px rgba(112, 0, 255, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.2);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ios-button:active {
  transform: scale(0.96);
  filter: brightness(0.9);
}

.ios-button-secondary {
  border-radius: 20px;
  font-weight: 700;
  color: #1a1a2e;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: all 0.2s;
}

.ios-button-secondary:hover {
  background: rgba(255, 255, 255, 0.8);
}

.ios-button-danger {
  border-radius: 20px;
  font-weight: 700;
  color: #ff3b30;
  background: rgba(255, 59, 48, 0.1);
  border: 1px solid rgba(255, 59, 48, 0.2);
  transition: all 0.2s;
}

.ios-button-danger:hover {
  background: #ff3b30;
  color: white;
}

.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07);
}

.glass-slider {
  background: rgba(0, 0, 0, 0.05);
}
</style>