<template>
    <div class="min-h-screen pt-12 pb-20 px-4 flex justify-center animate-fade-in">
      <div class="w-full max-w-2xl glass p-10 rounded-[40px] relative">
        
        <!-- Хедер -->
        <div class="text-center mb-10">
          <h1 class="text-3xl font-bold text-[#1a1a2e] mb-2">Новая услуга</h1>
          <p class="text-gray-500 text-sm">Создайте объявление и начните зарабатывать</p>
        </div>

        <!-- Форма -->
        <div class="space-y-6">
          
          <!-- Название -->
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
              Название услуги <span class="text-[#7000ff]">*</span>
            </label>
            <input 
              v-model="form.title" 
              placeholder="Например: Разработка сайта на Vue.js" 
              class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 transition-all text-lg font-medium text-[#1a1a2e] shadow-inner placeholder:text-gray-400"
              maxlength="100"
            >
            <div class="text-xs text-gray-400 mt-1 ml-2">{{ form.title.length }}/100</div>
          </div>

          <!-- Описание -->
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
              Описание <span class="text-[#7000ff]">*</span>
            </label>
            <textarea 
              v-model="form.description" 
              rows="6" 
              class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 resize-none text-gray-600 shadow-inner placeholder:text-gray-400"
              placeholder="Опишите что вы предлагаете, какие технологии используете, что входит в услугу..."
            ></textarea>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- Цена -->
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
                Цена (Руб.) <span class="text-[#7000ff]">*</span>
              </label>
              <input 
                v-model="form.price" 
                type="number" 
                min="1"
                class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 font-bold text-[#7000ff] shadow-inner"
                placeholder="100"
              >
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
                AI-шаблон
                <span class="ml-1 text-gray-400 font-normal cursor-help" title="Шаблон для автогенерации ТЗ. Если не заполнен - будет использован стандартный">ⓘ</span>
              </label>
              <textarea 
                v-model="form.ai_template" 
                rows="2"
                class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 text-sm shadow-inner resize-none placeholder:text-gray-400"
                placeholder="Опционально: промпт для AI при создании ТЗ"
              ></textarea>
            </div>
          </div>

          <!-- Теги -->
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
              Теги (для поиска)
            </label>
            <div class="bg-white/10 p-2 rounded-2xl border border-white/20 flex flex-wrap gap-2 min-h-[60px] shadow-inner">
              <span 
                v-for="(tag, idx) in form.tags" 
                :key="idx" 
                class="bg-[#1a1a2e] text-white px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-[#7000ff] transition-colors"
              >
                {{ tag }} 
                <button @click="removeTag(idx)" class="hover:text-red-300 text-lg leading-none">×</button>
              </span>
              
              <input 
                v-model="newTag" 
                @keydown.enter.prevent="addTag" 
                placeholder="Введите тег и нажмите Enter..." 
                class="bg-transparent outline-none text-sm py-1 px-2 flex-1 min-w-[150px] text-[#1a1a2e] placeholder:text-gray-400"
              >
            </div>
            <div class="text-xs text-gray-400 mt-1 ml-2">
              💡 Популярные теги: vue, react, python, дизайн, маркетинг
            </div>
          </div>

          <!-- Ошибка -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-4 animate-fade-in">
            <p class="text-red-600 text-sm font-bold">❌ {{ error }}</p>
          </div>

          <!-- Кнопка создания -->
          <button 
            @click="createService" 
            :disabled="loading || !isFormValid"
            class="w-full py-4 rounded-2xl font-bold shadow-lg transition-all border border-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
            :class="isFormValid && !loading ? 'bg-[#1a1a2e] text-white hover:scale-[1.01]' : 'bg-gray-300 text-gray-500'"
          >
            <span v-if="loading">⏳ Публикуем...</span>
            <span v-else-if="!isFormValid">⚠️ Заполните обязательные поля</span>
            <span v-else>🚀 Опубликовать услугу</span>
          </button>

          <!-- Превью -->
          <div v-if="isFormValid" class="bg-white/5 border border-white/10 rounded-2xl p-4 animate-fade-in">
            <div class="text-xs font-bold text-gray-400 uppercase mb-2">Превью:</div>
            <div class="bg-white/10 rounded-xl p-4">
              <h3 class="font-bold text-[#1a1a2e] mb-1">{{ form.title || 'Название услуги' }}</h3>
              <p class="text-sm text-gray-600 line-clamp-2">{{ form.description || 'Описание услуги' }}</p>
              <div class="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
                <div class="flex gap-2">
                  <span v-for="tag in form.tags.slice(0, 3)" :key="tag" class="px-2 py-1 bg-white/20 rounded text-xs text-gray-600">
                    #{{ tag }}
                  </span>
                </div>
                <div class="text-[#7000ff] font-bold">${{ form.price || '0' }}</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '../stores/authStore'
  
  const router = useRouter()
  const auth = useAuthStore()
  
  const form = ref({
    title: '',
    description: '',
    price: '',
    ai_template: '',
    tags: []
  })
  
  const newTag = ref('')
  const loading = ref(false)
  const error = ref('')
  
  // Валидация формы
  const isFormValid = computed(() => {
    return form.value.title.trim() !== '' &&
           form.value.description.trim() !== '' &&
           form.value.price && 
           parseFloat(form.value.price) > 0
  })
  
  // Добавление тега
  const addTag = () => {
    const tag = newTag.value.trim().toLowerCase()
    if (tag && !form.value.tags.includes(tag) && form.value.tags.length < 10) {
      form.value.tags.push(tag)
      newTag.value = ''
      error.value = ''
    }
  }
  
  // Удаление тега
  const removeTag = (idx) => {
    form.value.tags.splice(idx, 1)
  }
  
  // Создание услуги
  const createService = async () => {
    if (!isFormValid.value) {
      error.value = "Пожалуйста, заполните все обязательные поля"
      return
    }
    
    loading.value = true
    error.value = ''
    
    try {
      const payload = {
        ...form.value,
        price: parseFloat(form.value.price),
        // Данные владельца для отображения в карточке
        owner_name: auth.user.profile?.company_name || auth.user.profile?.full_name || 'Фрилансер',
        owner_avatar: auth.user.profile?.avatar || ''
      }
      
      await axios.post('/api/market/services/', payload)
      
      // Редирект в профиль после успеха
      router.push('/profile')
      
    } catch (e) {
      console.error('Create service error:', e)
      
      if (e.response?.status === 401) {
        error.value = "Ошибка авторизации. Войдите в аккаунт заново."
      } else if (e.response?.data?.error) {
        error.value = typeof e.response.data.error === 'object' 
          ? Object.values(e.response.data.error).flat().join(', ')
          : e.response.data.error
      } else {
        error.value = "Не удалось создать услугу. Попробуйте позже."
      }
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.15);
  }
  
  /* Анимация появления */
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fade-in {
    animation: fade-in 0.3s ease-out;
  }
  </style>