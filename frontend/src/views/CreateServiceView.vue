<template>
    <div class="min-h-screen pt-12 pb-20 px-4 flex justify-center animate-fade-in">
      <div class="w-full max-w-2xl glass p-10 rounded-[40px] relative">
        
        <div class="text-center mb-10">
          <h1 class="text-3xl font-bold text-[#1a1a2e] mb-2">
            {{ isEditing ? 'Редактирование услуги' : 'Новая услуга' }}
          </h1>
          <p class="text-gray-500 text-sm">
            {{ isEditing ? 'Обновите информацию о вашем предложении' : 'Создайте объявление и начните зарабатывать' }}
          </p>
        </div>

        <div class="space-y-6">
          
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

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
                Категория <span class="text-[#7000ff]">*</span>
              </label>
              <select 
                v-model="form.category" 
                class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 transition-all font-medium text-[#1a1a2e] shadow-inner cursor-pointer appearance-none"
              >
                <option value="development">Development</option>
                <option value="design">Design</option>
                <option value="marketing">Marketing</option>
                <option value="copywriting">Copywriting</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
                Минимальная цена за услугу (Руб) <span class="text-[#7000ff]">*</span>
              </label>
              <input 
                v-model="form.price" 
                type="number" 
                min="1"
                class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 font-bold text-[#7000ff] shadow-inner"
                placeholder="100"
              >
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 ml-2">
              Описание <span class="text-[#7000ff]">*</span>
            </label>
            <textarea 
              v-model="form.description" 
              rows="5" 
              class="w-full p-4 bg-white/10 rounded-2xl border border-white/20 outline-none focus:bg-white/20 resize-none text-gray-600 shadow-inner placeholder:text-gray-400"
              placeholder="Опишите что вы предлагаете, какие технологии используете, что входит в услугу..."
            ></textarea>
          </div>

          <div class="bg-[#7000ff]/5 border border-[#7000ff]/10 rounded-2xl p-6">
            <label class="block text-xs font-bold text-[#7000ff] uppercase tracking-wider mb-2 ml-1">
              Требования к заказчику (Бриф)
            </label>
            <p class="text-xs text-gray-500 mb-4 ml-1 leading-relaxed">
                Перечислите, что клиент <b>обязан</b> предоставить при заказе (цвета, референсы, доступы). 
                Это будет показано клиенту перед оплатой, чтобы нейросеть составила точное ТЗ.
            </p>
            <textarea 
              v-model="form.ai_template" 
              rows="3"
              class="w-full p-4 bg-white/50 rounded-xl border border-[#7000ff]/10 outline-none focus:bg-white/80 focus:border-[#7000ff]/30 resize-none text-[#1a1a2e] shadow-sm placeholder:text-gray-400 text-sm transition-all"
              placeholder="Пример: 1. Укажите цветовую гамму. 2. Пришлите ссылки на сайты, которые вам нравятся. 3. Есть ли у вас готовый логотип?"
            ></textarea>
          </div>

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
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-4 animate-fade-in">
            <p class="text-red-600 text-sm font-bold">❌ {{ error }}</p>
          </div>

          <button 
            @click="submitForm" 
            :disabled="loading || !isFormValid"
            class="w-full py-4 rounded-2xl font-bold shadow-lg transition-all border border-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
            :class="isFormValid && !loading ? 'bg-[#1a1a2e] text-white hover:scale-[1.01]' : 'bg-gray-300 text-gray-500'"
          >
            <span v-if="loading">⏳ {{ isEditing ? 'Сохранение...' : 'Публикация...' }}</span>
            <span v-else-if="!isFormValid">Заполните обязательные поля</span>
            <span v-else>{{ isEditing ? 'Сохранить изменения' : '🚀 Опубликовать услугу' }}</span>
          </button>

        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import axios from 'axios'
  import { useRouter, useRoute } from 'vue-router'
  import { useAuthStore } from '../stores/authStore'
  
  const router = useRouter()
  const route = useRoute()
  const auth = useAuthStore()
  
  const form = ref({
    title: '',
    description: '',
    price: '',
    category: 'development',
    ai_template: '',
    tags: []
  })
  
  const newTag = ref('')
  const loading = ref(false)
  const error = ref('')
  const isEditing = ref(false)
  
  // Валидация формы
  const isFormValid = computed(() => {
    return form.value.title.trim() !== '' &&
           form.value.description.trim() !== '' &&
           form.value.price && 
           parseFloat(form.value.price) > 0
  })
  
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

  // Загрузка данных для редактирования
  const fetchServiceData = async () => {
    if (route.name === 'edit-service' && route.params.id) {
        isEditing.value = true
        loading.value = true
        try {
            const res = await axios.get(`/api/market/services/${route.params.id}/`)
            const data = res.data.data
            // Проверка прав
            if (String(data.owner_id) !== String(auth.user.id)) {
                alert('Нет прав на редактирование')
                router.push('/profile')
                return
            }
            // Заполнение формы
            form.value = {
                title: data.title,
                description: data.description,
                price: data.price,
                category: data.category || 'development',
                ai_template: data.ai_template || '',
                tags: data.tags || []
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
      const payload = {
        ...form.value,
        price: parseFloat(form.value.price),
        owner_name: auth.user.profile?.company_name || auth.user.profile?.full_name || 'Фрилансер',
        owner_avatar: auth.user.profile?.avatar || ''
      }
      
      if (isEditing.value) {
          // UPDATE
          await axios.patch(`/api/market/services/${route.params.id}/`, payload)
          alert('Услуга успешно обновлена!')
          router.push(`/services/${route.params.id}`)
      } else {
          // CREATE
          await axios.post('/api/market/services/', payload)
          router.push('/profile')
      }
      
    } catch (e) {
      console.error('Save service error:', e)
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

  onMounted(() => {
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