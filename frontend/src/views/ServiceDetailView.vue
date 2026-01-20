<template>
  <div class="animate-fade-in pb-20 pt-6">
    <button @click="$router.back()" class="mb-6 flex items-center gap-2 text-gray-500 hover:text-[#7000ff] transition-colors font-medium ml-4">
      ← Назад
    </button>

    <div v-if="service" class="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto px-4">
      
      <div class="lg:col-span-2"> 
        <div class="glass overflow-hidden rounded-[40px] border border-white/20">
          
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

            <div v-if="service.images.length > 1" class="absolute inset-0 flex items-center justify-between p-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <button @click.stop="prevSlide" class="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center text-white hover:bg-white/40 transition-all">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 19l-7-7 7-7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
              <button @click.stop="nextSlide" class="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center text-white hover:bg-white/40 transition-all">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>

            <div v-if="service.images.length > 1" class="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
              <div 
                v-for="(_, index) in service.images" :key="index"
                class="h-1.5 rounded-full transition-all duration-300 shadow-sm"
                :class="currentSlide === index ? 'w-8 bg-white' : 'w-2 bg-white/40'"
              ></div>
            </div>
          </div>

          <div class="p-8 md:p-12">
            <div class="flex flex-col md:flex-row md:justify-between md:items-start gap-4 mb-8">
               <h1 class="text-3xl md:text-4xl font-black text-[#1a1a2e] leading-tight tracking-tight">
                 {{ service.title }}
               </h1>
               <span class="bg-[#7000ff]/10 text-[#7000ff] px-5 py-1.5 rounded-full text-xs font-black uppercase tracking-widest self-start whitespace-nowrap">
                 {{ service.category || 'Development' }}
               </span>
            </div>
            
            <div class="prose max-w-none text-gray-900 leading-[1.8] whitespace-pre-line mb-10 text-lg">
              {{ service.description }}
            </div>

            <div class="flex flex-wrap gap-2 pt-8 border-t border-gray-100">
              <span v-for="tag in service.tags" :key="tag" class="px-4 py-2 rounded-xl bg-gray-100/50 text-gray-500 text-sm font-bold border border-white/20 shadow-sm">
                #{{ tag }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-8 animate-fade-in">
          <ReviewsSection :worker-id="String(service.owner_id)" @reviews-loaded="onReviewsLoaded" />
        </div>
      </div>

      <div class="space-y-6">
        <div class="ios-glass-card p-8 sticky top-24">
          <div class="text-3xl font-black text-[#7000ff] mb-2 drop-shadow-sm">{{ service.price }} ₽</div>
          <p class="text-gray-500 text-xs font-bold uppercase tracking-widest mb-8">Начальная цена</p>
          
          <div v-if="isOwner" class="space-y-4">
             <div class="ios-inner-inset p-4 flex items-center gap-3 mb-4">
               <div class="w-8 h-8 rounded-full bg-[#1a1a2e] flex items-center justify-center text-white">
                 <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
               </div>
               <span class="text-[10px] font-black text-[#1a1a2e] uppercase tracking-wider">Это ваше объявление</span>
             </div>
             
             <button @click="$router.push(`/my-services/edit/${service.id}`)" class="ios-button-secondary py-4 w-full">
               Редактировать
             </button>

             <button @click="deleteService" class="ios-button-danger py-4 w-full">
               Удалить
             </button>
          </div>

          <div v-else>
            <button @click="showWizard = true" class="ios-button py-4 w-full">
              Начать сделку с AI
            </button>
            
            <div class="mt-10 pt-8 border-t border-black/5">
              <div class="flex items-center gap-4 cursor-pointer group hover:bg-black/5 -m-2 p-3 rounded-[24px] transition-all" @click="goToOwnerProfile">
                <UserAvatar :avatar-url="service.owner_avatar" :name="service.owner_name || 'Пользователь'" size="lg" class="border-2 border-white shadow-sm group-hover:ring-2 group-hover:ring-[#7000ff] transition-all" />
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-[#1a1a2e] group-hover:text-[#7000ff] transition-colors truncate tracking-tight">{{ service.owner_name || 'Пользователь' }}</div>
                  <div class="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-2">
                    <span>Профиль автора</span>
                    <span v-if="workerRating > 0" class="text-[#7000ff] font-black">★ {{ workerRating.toFixed(1) }}</span>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" stroke-width="2.5" /></svg>
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
/* ГЛАВНЫЙ ЭФФЕКТ: IOS THICK GLASS */
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
  font-size: 17px;
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
  border-radius: 24px;
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
  border-radius: 24px;
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