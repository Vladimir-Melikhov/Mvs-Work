<template>
    <div class="reviews-section">
      <div class="flex items-center justify-between mb-6 px-2">
        <h3 class="text-xl font-bold text-[#1a1a2e]">Отзывы</h3>
        
        <div v-if="reviews.length > 0" class="flex items-center gap-3">
          <div class="flex gap-1">
            <div v-for="i in 5" :key="'avg-' + i" class="relative w-4 h-4">
               <svg class="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                 <defs>
                   <linearGradient :id="'avg-grad-' + i">
                     <stop offset="0%" stop-color="#7000ff" />
                     <stop 
                       :offset="(Math.min(Math.max(averageRating - (i - 1), 0), 1) * 100) + '%'" 
                       stop-color="#7000ff" 
                     />
                     <stop 
                       :offset="(Math.min(Math.max(averageRating - (i - 1), 0), 1) * 100) + '%'" 
                       stop-color="#e5e7eb" 
                     />
                     <stop offset="100%" stop-color="#e5e7eb" />
                   </linearGradient>
                 </defs>
                 <path 
                   d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
                   :fill="'url(#avg-grad-' + i + ')'"
                 />
               </svg>
            </div>
          </div>
          <div class="text-xs font-bold text-gray-400">
            <span class="text-[#1a1a2e]">{{ averageRating.toFixed(1) }}</span>
            <span class="mx-1">·</span>
            <span>{{ reviews.length }} шт.</span>
          </div>
        </div>
      </div>
  
      <div v-if="loading" class="text-center py-10 opacity-50">
        <div class="w-8 h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin mx-auto"></div>
      </div>
  
      <div v-else-if="reviews.length === 0" class="glass p-10 rounded-[32px] text-center border border-white/20 opacity-70">
        <div class="mx-auto w-12 h-12 text-gray-300 mb-3">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
            </svg>
        </div>
        <p class="font-bold text-[#1a1a2e] mb-1">Отзывов пока нет</p>
        <p class="text-xs text-gray-500">Здесь появятся оценки от клиентов</p>
      </div>
  
      <div v-else class="space-y-4">
        <div 
          v-for="review in reviews" 
          :key="review.id"
          class="glass rounded-[24px] p-6 border border-white/20"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-xs font-bold shadow-md">
                {{ getInitials(review.reviewer_name) }}
              </div>
              <div>
                <div class="font-bold text-[#1a1a2e] text-sm">{{ review.reviewer_name || 'Клиент' }}</div>
                <div class="text-[10px] text-gray-400 font-bold uppercase tracking-wider">{{ formatDate(review.created_at) }}</div>
              </div>
            </div>
            
            <div class="flex gap-0.5">
                <div v-for="i in 5" :key="review.id + '-star-' + i" class="relative w-3.5 h-3.5">
                  <svg class="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <linearGradient :id="'grad-' + review.id + '-' + i">
                        <stop offset="0%" stop-color="#7000ff" />
                        <stop 
                          :offset="(Math.min(Math.max(review.rating - (i - 1), 0), 1) * 100) + '%'" 
                          stop-color="#7000ff" 
                        />
                        <stop 
                          :offset="(Math.min(Math.max(review.rating - (i - 1), 0), 1) * 100) + '%'" 
                          stop-color="#e5e7eb" 
                        />
                        <stop offset="100%" stop-color="#e5e7eb" />
                      </linearGradient>
                    </defs>
                    <path 
                      d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
                      :fill="'url(#grad-' + review.id + '-' + i + ')'"
                    />
                  </svg>
                </div>
            </div>
          </div>
  
          <p v-if="review.comment" class="text-gray-600 text-xs leading-relaxed md:pl-13">
            {{ review.comment }}
          </p>
          <p v-else class="text-gray-400 text-xs italic md:pl-13">Без комментария</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import axios from 'axios'
  
  const props = defineProps({
    workerId: {
      type: String,
      required: true
    }
  })
  
  const reviews = ref([])
  const loading = ref(true)
  
  const averageRating = computed(() => {
    if (reviews.value.length === 0) return 0
    const sum = reviews.value.reduce((acc, r) => acc + Number(r.rating), 0)
    return sum / reviews.value.length
  })
  
  const emit = defineEmits(['reviews-loaded'])
  
  const fetchReviews = async () => {
    loading.value = true
    try {
      const res = await axios.get(`/api/market/reviews/by-worker/${props.workerId}/`)
      if (res.data.status === 'success') {
        const rawReviews = res.data.data
        const reviewerIds = [...new Set(rawReviews.map(r => r.reviewer_id))]
        
        if (reviewerIds.length > 0) {
          try {
            const usersRes = await axios.post('/api/auth/users/batch/', {
              user_ids: reviewerIds
            })
            
            const usersMap = {}
            if (usersRes.data.status === 'success') {
              usersRes.data.data.forEach(user => {
                usersMap[user.id] = user.name
              })
            }
            
            reviews.value = rawReviews.map(review => ({
              ...review,
              reviewer_name: usersMap[review.reviewer_id] || 'Клиент'
            }))
          } catch (err) {
            console.error('Batch user fetch failed', err)
            reviews.value = rawReviews
          }
        } else {
          reviews.value = rawReviews
        }
        
        emit('reviews-loaded', {
          averageRating: averageRating.value,
          totalReviews: reviews.value.length
        })
      }
    } catch (e) {
      console.error('Failed to fetch reviews:', e)
    } finally {
      loading.value = false
    }
  }
  
  const getInitials = (name) => {
    return name ? name.substring(0, 1).toUpperCase() : 'К'
  }
  
  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
  }
  
  onMounted(() => {
    fetchReviews()
  })
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07);
  }
  
  /* Отступ для текста комментария, чтобы он был под именем (только на десктопах) */
  @media (min-width: 768px) {
    .pl-13 {
      padding-left: 3.25rem;
    }
  }
  </style>