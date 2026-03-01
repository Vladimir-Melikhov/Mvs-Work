<template>
  <div class="min-h-screen pt-4 md:pt-12 pb-20 px-3 md:px-4 flex justify-center animate-fade-in">
    <div class="w-full max-w-2xl glass p-4 md:p-10 rounded-[32px] md:rounded-[40px] relative">
      
      <div class="text-center mb-6 md:mb-10">
        <h1 class="text-xl md:text-3xl font-bold text-[#1a1a2e] mb-2">
          {{ isEditing ? 'Редактирование услуги' : 'Новая услуга' }}
        </h1>
        <p class="text-gray-500 text-xs md:text-sm">
          {{ isEditing ? 'Обновите информацию о вашем предложении' : 'Создайте объявление и начните зарабатывать' }}
        </p>
      </div>

      <div class="space-y-4 md:space-y-6">
        
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-2">
            Название услуги <span class="text-[#7000ff]">*</span>
          </label>
          <input 
            v-model="form.title" 
            placeholder="Например: Разработка сайта на Vue.js" 
            class="w-full p-3 md:p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 transition-all text-sm md:text-lg font-medium text-[#1a1a2e] shadow-inner placeholder:text-gray-400"
            maxlength="100"
          >
          <div class="text-xs text-gray-400 mt-1 ml-2">{{ form.title.length }}/100</div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
           <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-2">
              Категория <span class="text-[#7000ff]">*</span>
            </label>
            <select 
              v-model="form.category" 
              @change="onCategoryChange"
              class="w-full p-3 md:p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 transition-all font-medium text-[#1a1a2e] shadow-inner cursor-pointer appearance-none text-sm md:text-base"
            >
              <option value="development">Разработка</option>
              <option value="design">Дизайн</option>
              <option value="marketing">Маркетинг</option>
              <option value="writing">Копирайтинг</option>
              <option value="video">Видео</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-2">
              Подкатегория
            </label>
            <select 
              v-model="form.subcategory" 
              :disabled="!availableSubcategories.length"
              class="w-full p-3 md:p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 transition-all font-medium text-[#1a1a2e] shadow-inner cursor-pointer appearance-none text-sm md:text-base disabled:opacity-50"
            >
              <option value="">Не выбрана</option>
              <option v-for="subcat in availableSubcategories" :key="subcat.value" :value="subcat.value">
                {{ subcat.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-2">
              Мин. цена (₽) <span class="text-[#7000ff]">*</span>
            </label>
            <input 
              v-model="form.price" 
              type="number" 
              min="1"
              class="w-full p-3 md:p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 font-bold text-[#7000ff] shadow-inner text-sm md:text-base"
              placeholder="100"
            >
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-2">
            Описание <span class="text-[#7000ff]">*</span>
          </label>
          <textarea 
            v-model="form.description" 
            rows="5" 
            class="w-full p-3 md:p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 resize-none text-gray-600 shadow-inner placeholder:text-gray-400 text-xs md:text-base"
            placeholder="Опишите что вы предлагаете, какие технологии используете, что входит в услугу..."
          ></textarea>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 ml-2">
            Изображения услуги (до 5 шт, первое - обложка)
          </label>
          
          <div class="grid grid-cols-3 md:grid-cols-3 gap-2 md:gap-3">
            <div 
              v-for="i in 5" 
              :key="i"
              class="relative aspect-square rounded-xl md:rounded-2xl border-2 border-dashed border-white/30 overflow-hidden group hover:border-[#7000ff]/50 transition-all"
            >
              <img 
                v-if="imagePreviews[i-1]" 
                :src="imagePreviews[i-1]" 
                class="w-full h-full object-cover"
              >
              
              <label 
                class="absolute inset-0 cursor-pointer flex items-center justify-center bg-white/5 group-hover:bg-white/10 transition-all"
                :class="{'bg-black/40': imagePreviews[i-1]}"
              >
                <div class="text-center">
                  <svg 
                    v-if="!imagePreviews[i-1]"
                    class="w-6 md:w-8 h-6 md:h-8 mx-auto text-gray-400 group-hover:text-[#7000ff] transition-colors" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <div 
                    v-else
                    class="text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <svg class="w-5 md:w-6 h-5 md:h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
                <input 
                  type="file" 
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  @change="(e) => handleImageUpload(e, i-1)"
                  class="hidden"
                >
              </label>
              
              <button 
                v-if="imagePreviews[i-1]"
                @click="removeImage(i-1)"
                class="absolute top-1 right-1 w-5 h-5 md:w-6 md:h-6 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-xs md:text-base"
              >
                ×
              </button>
            </div>
          </div>
          
          <p class="text-[10px] md:text-xs text-gray-400 mt-2 ml-2">JPG, PNG, GIF, WEBP • До 5MB каждое</p>
        </div>

        <div class="bg-[#7000ff]/5 border border-[#7000ff]/10 rounded-xl md:rounded-2xl p-3 md:p-6">
          <label class="block text-xs font-bold text-[#7000ff] uppercase tracking-wider mb-2 ml-1">
            Требования к заказчику (Бриф)
          </label>
          <p class="text-[10px] md:text-xs text-gray-500 mb-3 md:mb-4 ml-1 leading-relaxed break-words">
              Перечислите, что клиент <b>обязан</b> предоставить при заказе (цвета, референсы, доступы). 
              Это будет показано клиенту перед оплатой, чтобы нейросеть составила точное ТЗ.
          </p>
          <textarea 
            v-model="form.ai_template" 
            rows="3"
            class="w-full p-3 md:p-4 bg-white/50 rounded-xl border border-[#7000ff]/10 outline-none focus:bg-white/80 focus:border-[#7000ff]/30 resize-none text-[#1a1a2e] shadow-sm placeholder:text-gray-400 text-xs md:text-sm transition-all"
            placeholder="Пример: 1. Укажите цветовую гамму. 2. Пришлите ссылки на сайты, которые вам нравятся. 3. Есть ли у вас готовый логотип?"
          ></textarea>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-2">
            Теги (для поиска)
          </label>
          <div class="bg-white/10 p-2 rounded-2xl border border-white/20 flex flex-wrap gap-2 min-h-[60px] shadow-inner">
            <span 
              v-for="(tag, idx) in form.tags" 
              :key="idx" 
              class="bg-[#1a1a2e] text-white px-2 md:px-3 py-1 md:py-1.5 rounded-lg md:rounded-xl text-[10px] md:text-xs font-bold flex items-center gap-1 md:gap-2 hover:bg-[#7000ff] transition-colors break-words"
            >
              {{ tag }} 
              <button @click="removeTag(idx)" class="hover:text-red-300 text-sm md:text-lg leading-none">×</button>
            </span>
            
            <input 
              v-model="newTag" 
              @keydown.enter.prevent="addTag" 
              placeholder="Введите тег и нажмите Enter..." 
              class="bg-transparent outline-none text-xs md:text-sm py-1 px-2 flex-1 min-w-[120px] text-[#1a1a2e] placeholder:text-gray-400"
            >
          </div>
        </div>

        <div v-if="auth.user?.role === 'worker'" class="bg-white/10 rounded-xl md:rounded-2xl p-3 md:p-4 border border-white/20">
          <label class="flex items-start gap-2 md:gap-3 cursor-pointer group">
            <input 
              type="checkbox" 
              v-model="form.is_active"
              :disabled="!hasActiveSubscription"
              class="mt-0.5 md:mt-1 w-4 h-4 md:w-5 md:h-5 rounded border-2 border-gray-300 text-[#7000ff] focus:ring-[#7000ff] disabled:opacity-50 disabled:cursor-not-allowed"
            >
            <div class="flex-1">
              <div class="font-bold text-[#1a1a2e] group-hover:text-[#7000ff] transition-colors text-xs md:text-base">
                {{ isEditing ? 'Активное объявление' : 'Опубликовать сразу' }}
              </div>
              <div class="text-[10px] md:text-sm text-gray-600 mt-1">
                {{ hasActiveSubscription 
                  ? 'Объявление будет доступно в общей ленте' 
                  : 'Для публикации требуется активная подписка' 
                }}
              </div>
              <button 
                v-if="!hasActiveSubscription"
                type="button"
                @click.stop="showSubscriptionModal = true"
                class="text-[10px] md:text-xs font-bold text-[#7000ff] hover:underline mt-2"
              >
                Активировать подписку →
              </button>
            </div>
          </label>
        </div>

        <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl md:rounded-2xl p-3 md:p-4 animate-fade-in">
          <p class="text-red-600 text-xs md:text-sm font-bold break-words">❌ {{ error }}</p>
        </div>

        <button 
          @click="submitForm" 
          :disabled="loading || !isFormValid"
          class="w-full py-3 md:py-4 rounded-xl md:rounded-2xl font-bold shadow-lg transition-all border border-white/10 disabled:opacity-50 disabled:cursor-not-allowed text-xs md:text-base"
          :class="isFormValid && !loading ? 'bg-[#1a1a2e] text-white hover:scale-[1.01]' : 'bg-gray-300 text-gray-500'"
        >
          <span v-if="loading">⏳ {{ isEditing ? 'Сохранение...' : 'Публикация...' }}</span>
          <span v-else-if="!isFormValid">Заполните обязательные поля</span>
          <span v-else>{{ isEditing ? 'Сохранить изменения' : '🚀 Опубликовать услугу' }}</span>
        </button>

      </div>
    </div>

    <SubscriptionModal 
      v-if="showSubscriptionModal" 
      @close="showSubscriptionModal = false"
      @subscribed="handleSubscribed"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import SubscriptionModal from '../components/SubscriptionModal.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = ref({
  title: '',
  description: '',
  price: '',
  category: 'development',
  subcategory: '',
  ai_template: '',
  tags: [],
  is_active: false  // ✅ ИСПРАВЛЕНО: по умолчанию false
})

const imageFiles = ref([null, null, null, null, null])
const imagePreviews = ref([null, null, null, null, null])
const existingImages = ref([])

const newTag = ref('')
const loading = ref(false)
const error = ref('')
const isEditing = ref(false)
const showSubscriptionModal = ref(false)

const subcategoriesMap = ref({})
const availableSubcategories = computed(() => {
  return subcategoriesMap.value[form.value.category] || []
})

const hasActiveSubscription = computed(() => {
  if (auth.user?.role !== 'worker') return true
  return auth.user?.subscription?.is_active || false
})

const isFormValid = computed(() => {
  return form.value.title.trim() !== '' &&
         form.value.description.trim() !== '' &&
         form.value.price && 
         parseFloat(form.value.price) > 0
})

const onCategoryChange = () => {
  form.value.subcategory = ''
}

const handleImageUpload = (event, index) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (file.size > 5 * 1024 * 1024) {
    error.value = 'Изображение слишком большое. Максимум 5MB'
    return
  }
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    error.value = 'Неподдерживаемый формат. Используйте JPG, PNG, GIF или WEBP'
    return
  }
  
  imageFiles.value[index] = file
  error.value = ''
  
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreviews.value[index] = e.target.result
  }
  reader.readAsDataURL(file)
}

const removeImage = (index) => {
  imageFiles.value[index] = null
  imagePreviews.value[index] = null
  
  if (isEditing.value && existingImages.value[index]) {
    deleteExistingImage(existingImages.value[index].id)
  }
}

const deleteExistingImage = async (imageId) => {
  try {
    await axios.delete(`/api/market/services/${route.params.id}/delete-image/${imageId}/`)
  } catch (e) {
    console.error('Failed to delete image:', e)
  }
}

const addTag = () => {
  const tag = newTag.value.trim().toLowerCase()
  if (tag && !form.value.tags.includes(tag) && form.value.tags.length < 10) {
    form.value.tags.push(tag)
    newTag.value = ''
    error.value = ''
  }
}

const removeTag = (idx) => {
  form.value.tags.splice(idx, 1)
}

const fetchSubcategories = async () => {
  try {
    const res = await axios.get('/api/market/services/subcategories/')
    if (res.data.status === 'success') {
      subcategoriesMap.value = res.data.data
    }
  } catch (e) {
    console.error('Ошибка загрузки подкатегорий:', e)
  }
}

const fetchServiceData = async () => {
  if (route.name === 'edit-service' && route.params.id) {
      isEditing.value = true
      loading.value = true
      try {
          const res = await axios.get(`/api/market/services/${route.params.id}/`)
          const data = res.data.data
          if (String(data.owner_id) !== String(auth.user.id)) {
              alert('Нет прав на редактирование')
              router.push('/profile')
              return
          }
          form.value = {
              title: data.title,
              description: data.description,
              price: data.price,
              category: data.category || 'development',
              subcategory: data.subcategory || '',
              ai_template: data.ai_template || '',
              tags: data.tags || [],
              is_active: data.is_active !== undefined ? data.is_active : false
          }
          
          if (data.images && data.images.length > 0) {
            existingImages.value = data.images
            data.images.forEach((img, idx) => {
              if (idx < 5) {
                imagePreviews.value[idx] = img.image_url
              }
            })
          }
      } catch (e) {
          console.error("Fetch error", e)
          error.value = "Ошибка загрузки данных услуги"
      } finally {
          loading.value = false
      }
  }
}

const submitForm = async () => {
  if (!isFormValid.value) {
    error.value = "Пожалуйста, заполните все обязательные поля"
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const formData = new FormData()
    
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('price', parseFloat(form.value.price))
    formData.append('category', form.value.category)
    formData.append('subcategory', form.value.subcategory || '')
    formData.append('ai_template', form.value.ai_template || '')
    formData.append('tags', JSON.stringify(form.value.tags))
    
    // ✅ ИСПРАВЛЕНО: Передаем выбор пользователя
    formData.append('is_active', form.value.is_active ? 'true' : 'false')
    
    if (!isEditing.value) {
      formData.append('owner_name', auth.user.profile?.company_name || auth.user.profile?.full_name || 'Фрилансер')
      formData.append('owner_avatar', auth.user.profile?.avatar_url || '')
    }
    
    imageFiles.value.forEach((file, idx) => {
      if (file) {
        formData.append(`image_${idx}`, file)
      }
    })
    
    if (isEditing.value) {
        const response = await axios.patch(`/api/market/services/${route.params.id}/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.require_subscription) {
          showSubscriptionModal.value = true
          return
        }
        
        alert('Услуга успешно обновлена!')
        router.push(`/services/${route.params.id}`)
    } else {
        const response = await axios.post('/api/market/services/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.message) {
          alert(response.data.message)
        }
        
        router.push('/profile')
    }
    
  } catch (e) {
    console.error('Save service error:', e)
    
    if (e.response?.data?.require_subscription) {
      showSubscriptionModal.value = true
      return
    }
    
    if (e.response?.data?.error) {
      error.value = typeof e.response.data.error === 'object' 
        ? Object.values(e.response.data.error).flat().join(', ')
        : e.response.data.error
    } else {
      error.value = "Не удалось сохранить услугу. Попробуйте позже."
    }
  } finally {
    loading.value = false
  }
}

const handleSubscribed = async () => {
  showSubscriptionModal.value = false
  await auth.fetchProfile()
  form.value.is_active = true
}

onMounted(() => {
    fetchSubcategories()
    fetchServiceData()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.15);
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
</style>
