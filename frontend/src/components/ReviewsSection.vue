<template>
    <div class="reviews-section">
      <div class="flex items-center justify-between mb-6 px-2">
        <h3 class="text-xl font-bold text-[#1a1a2e]">Отзывы</h3>
        <div v-if="reviews.length > 0" class="flex items-center gap-2">
          <div class="flex">
            <span 
              v-for="star in 5" 
              :key="star"
              class="text-2xl"
            >
              <span v-if="star <= Math.round(averageRating)" class="text-yellow-400">⭐</span>
              <span v-else class="text-gray-300">☆</span>
            </span>
          </div>
          <div class="text-sm">
            <div class="font-bold text-[#1a1a2e]">{{ averageRating.toFixed(1) }}</div>
            <div class="text-gray-500">{{ reviews.length }} отзывов</div>
          </div>
        </div>
      </div>
  
      <div v-if="loading" class="text-center py-10 opacity-50">
        <div class="w-8 h-8 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin mx-auto"></div>
      </div>
  
      <div v-else-if="reviews.length === 0" class="glass p-8 rounded-[32px] text-center border border-white/20 opacity-70">
        <div class="text-5xl mb-3 opacity-30">⭐</div>
        <p class="font-bold text-[#1a1a2e] mb-2">Отзывов пока нет</p>
        <p class="text-sm text-gray-500">Завершите первый заказ, чтобы получить отзыв</p>
      </div>
  
      <div v-else class="space-y-4">
        <div 
          v-for="review in reviews" 
          :key="review.id"
          class="glass rounded-[24px] p-6 border border-white/20"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-sm font-bold">
                {{ getInitials(review.reviewer_name) }}
              </div>
              <div>
                <div class="font-bold text-[#1a1a2e]">{{ review.reviewer_name || 'Клиент' }}</div>
                <div class="text-xs text-gray-500">{{ formatDate(review.created_at) }}</div>
              </div>
            </div>
            
            <div class="flex">
              <span 
                v-for="star in 5" 
                :key="star"
                class="text-lg"
              >
                <span v-if="star <= review.rating" class="text-yellow-400">⭐</span>
                <span v-else class="text-gray-300">☆</span>
              </span>
            </div>
          </div>
  
          <p v-if="review.comment" class="text-gray-600 text-sm leading-relaxed">
            {{ review.comment }}
          </p>
          <p v-else class="text-gray-400 text-sm italic">Без комментария</p>
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
    const sum = reviews.value.reduce((acc, r) => acc + r.rating, 0)
    return sum / reviews.value.length
  })
  
  const emit = defineEmits(['reviews-loaded'])
  
  const fetchReviews = async () => {
    loading.value = true
    try {
      const res = await axios.get(`/api/market/reviews/by-worker/${props.workerId}/`)
      if (res.data.status === 'success') {
        // Получаем имена ревьюверов
        const reviewerIds = [...new Set(res.data.data.map(r => r.reviewer_id))]
        
        if (reviewerIds.length > 0) {
          const usersRes = await axios.post('/api/auth/users/batch/', {
            user_ids: reviewerIds
          })
          
          const usersMap = {}
          if (usersRes.data.status === 'success') {
            usersRes.data.data.forEach(user => {
              usersMap[user.id] = user.name
            })
          }
          
          reviews.value = res.data.data.map(review => ({
            ...review,
            reviewer_name: usersMap[review.reviewer_id] || 'Клиент'
          }))
        } else {
          reviews.value = res.data.data
        }
        
        // ✅ Отправляем рейтинг родителю
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
  </style>