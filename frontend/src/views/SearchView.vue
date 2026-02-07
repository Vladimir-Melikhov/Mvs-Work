<!-- frontend/src/views/SearchView.vue -->
<template>
  <div class="min-h-screen pt-4 pb-24 md:pb-20">
    <div class="text-center mb-8 md:mb-12 px-4">
      <h1 class="text-2xl md:text-4xl font-bold text-[#1a1a2e] mb-4 md:mb-6 tracking-tight leading-tight">
        Поиск идеального<br class="md:hidden"> исполнителя + AI
      </h1>
      
      <div class="max-w-2xl mx-auto relative">
        <div class="glass p-1.5 md:p-2 rounded-full flex items-center shadow-xl transition-all focus-within:bg-white/20 focus-within:border-white/40 focus-within:shadow-2xl">
           <span class="pl-3 md:pl-6 text-lg md:text-xl opacity-50">🔍</span>
           <input 
             v-model="searchQuery"
             @keydown.enter="handleSearch"
             placeholder="Что нужно сделать?" 
             class="w-full bg-transparent border-none outline-none text-sm md:text-lg p-2 md:p-4 placeholder-gray-500 text-[#1a1a2e] font-medium"
           >
           <button 
             @click="handleSearch"
             class="bg-[#1a1a2e] text-white px-4 md:px-8 py-2 md:py-3 rounded-full font-bold hover:bg-[#7000ff] transition-colors shadow-md mr-1 text-xs md:text-base whitespace-nowrap"
           >
             Найти
           </button>
        </div>
      </div>
      
      <!-- Категории и подкатегории -->
      <div class="flex justify-center gap-1.5 md:gap-2 mt-6 md:mt-8 flex-wrap px-2">
         <!-- Показываем основные категории если нет выбранной или подкатегории -->
         <template v-if="!selectedCategory">
           <button 
             v-for="cat in categories" 
             :key="cat.value" 
             @click="selectCategory(cat.value)"
             @mouseenter="hoverCategory = cat.value"
             @mouseleave="hoverCategory = null"
             class="px-3 md:px-5 py-2 rounded-full text-[10px] md:text-sm font-bold transition-all border glass-chip text-gray-600 hover:bg-white/30 hover:text-[#1a1a2e] border-white/20"
           >
             {{ cat.label }}
           </button>
         </template>
         
         <!-- Показываем подкатегории выбранной категории -->
         <template v-else>
           <button 
             @click="clearCategory"
             class="px-3 md:px-5 py-2 rounded-full text-[10px] md:text-sm font-bold transition-all border bg-gray-200 text-gray-700 hover:bg-gray-300 border-gray-300"
           >
             ← {{ getCategoryLabel(selectedCategory) }}
           </button>
           
           <button 
             v-for="subcat in currentSubcategories" 
             :key="subcat.value" 
             @click="toggleSubcategory(subcat.value)"
             class="px-3 md:px-5 py-2 rounded-full text-[10px] md:text-sm font-bold transition-all border"
             :class="selectedSubcategories.includes(subcat.value)
               ? 'bg-[#7000ff] text-white border-[#7000ff] shadow-lg' 
               : 'glass-chip text-gray-600 hover:bg-white/30 hover:text-[#1a1a2e] border-white/20'"
           >
             {{ subcat.label }}
           </button>
         </template>
         
         <button 
           v-if="selectedCategory || selectedSubcategories.length > 0"
           @click="clearFilters"
           class="px-3 md:px-5 py-2 rounded-full glass-chip text-[10px] md:text-sm font-bold text-red-500 hover:bg-red-50 transition-all border border-red-200"
         >
           ✕
         </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-20">
      <div class="inline-block w-10 h-10 md:w-12 md:h-12 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
      <p class="mt-4 text-sm text-gray-500">Загрузка...</p>
    </div>

    <div v-else-if="paginatedServices.length > 0">
      <div class="grid grid-cols-2 lg:grid-cols-3 gap-3 md:gap-6 animate-fade-in px-3 md:px-6">
        <div 
          v-for="service in paginatedServices" 
          :key="service.id" 
          class="glass rounded-[20px] md:rounded-[32px] overflow-hidden hover:bg-white/20 transition-all cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1"
          @click="$router.push(`/services/${service.id}`)"
        >
          <div v-if="service.images && service.images.length > 0" class="relative aspect-video overflow-hidden">
            <img 
              :src="service.images[0].image_url" 
              class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              alt="Service preview"
            >
            <div v-if="service.images.length > 1" class="absolute bottom-1.5 md:bottom-2 right-1.5 md:right-2 px-1.5 py-0.5 rounded-lg bg-black/40 backdrop-blur-md text-white text-[8px] md:text-[10px] font-bold border border-white/20">
              +{{ service.images.length - 1 }}
            </div>
          </div>
          <div v-else class="aspect-video bg-gray-100 flex items-center justify-center text-gray-300">
             <svg class="w-8 h-8 md:w-12 md:h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>

          <div class="p-3 md:p-6 flex flex-col flex-1">
            <div class="flex items-center justify-between gap-2 mb-2 md:mb-4">
              <div class="flex items-center gap-2 flex-1 min-w-0">
                <UserAvatar :avatar-url="service.owner_avatar" :name="service.owner_name" size="xs" class="shrink-0" />
                
                <div class="flex-1 min-w-0">
                   <div class="text-xs md:text-sm font-bold text-[#1a1a2e] line-clamp-1 leading-tight">{{ service.owner_name || 'Мастер' }}</div>
                   <div class="text-[8px] md:text-[10px] text-gray-500 font-bold uppercase tracking-wider truncate">
                     {{ service.subcategory_display || getCategoryLabel(service.category) || 'Услуга' }}
                   </div>
                </div>
              </div>
              
              <div class="text-[#7000ff] font-bold text-xs md:text-lg shrink-0 whitespace-nowrap">{{ Math.floor(service.price) }}₽</div>
            </div>

            <h3 class="text-sm md:text-xl font-bold text-[#1a1a2e] mb-1.5 md:mb-2 leading-tight group-hover:text-[#7000ff] transition-colors line-clamp-2 break-words">
              {{ service.title }}
            </h3>

            <p class="text-gray-600 text-[10px] md:text-sm leading-relaxed mb-3 md:mb-4 line-clamp-2 flex-1 break-words">
              {{ service.description }}
            </p>

            <div class="flex items-center justify-between mt-auto pt-2 md:pt-4 border-t border-white/10 gap-2">
               <div class="flex flex-wrap gap-1 flex-1 min-w-0">
                  <span v-for="tag in service.tags?.slice(0, 1)" :key="tag" class="px-2 py-0.5 rounded-md bg-white/20 text-[8px] md:text-xs font-bold text-gray-500 border border-white/20 truncate">
                    #{{ tag }}
                  </span>
               </div>
               
               <div v-if="service.owner_rating > 0" class="flex items-center gap-0.5 bg-[#7000ff]/5 px-1.5 py-0.5 md:px-3 md:py-1.5 rounded-lg border border-[#7000ff]/10 shrink-0">
                 <span class="text-[#7000ff] text-[8px] md:text-xs font-black">★</span>
                 <span class="text-[#7000ff] text-[8px] md:text-xs font-black tracking-tight">
                   {{ Number(service.owner_rating).toFixed(1) }}
                 </span>
               </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="flex justify-center items-center gap-2 mt-8 md:mt-12 mb-8">
        <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1" class="w-8 h-8 md:w-10 md:h-10 rounded-full glass flex items-center justify-center disabled:opacity-30 text-sm md:text-base">←</button>
        <div class="flex gap-1 md:gap-2">
          <button 
            v-for="page in totalPages" :key="page" @click="changePage(page)"
            class="w-8 h-8 md:w-10 md:h-10 rounded-full font-bold text-xs md:text-sm transition-all"
            :class="currentPage === page ? 'bg-[#1a1a2e] text-white' : 'glass'"
          >
            {{ page }}
          </button>
        </div>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages" class="w-8 h-8 md:w-10 md:h-10 rounded-full glass flex items-center justify-center disabled:opacity-30 text-sm md:text-base">→</button>
      </div>
    </div>
    
    <div v-else class="text-center py-20 opacity-50 px-4">
       <div class="text-4xl md:text-6xl mb-4">🌪️</div>
       <p class="font-bold text-[#1a1a2e]">Ничего не найдено</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import UserAvatar from '../components/UserAvatar.vue'

const services = ref([]) 
const allServices = ref([]) 
const searchQuery = ref('')
const loading = ref(false)
const selectedCategory = ref(null)
const selectedSubcategories = ref([])
const hoverCategory = ref(null)
const subcategoriesMap = ref({})
const currentPage = ref(1)
const itemsPerPage = 8

const categories = [
  { label: 'Дизайн', value: 'design' },
  { label: 'Разработка', value: 'development' },
  { label: 'Тексты', value: 'writing' },
  { label: 'Маркетинг', value: 'marketing' },
  { label: 'Видео', value: 'video' },
]

const currentSubcategories = computed(() => {
  if (!selectedCategory.value) return []
  return subcategoriesMap.value[selectedCategory.value] || []
})

const totalPages = computed(() => Math.ceil(services.value.length / itemsPerPage))
const paginatedServices = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return services.value.slice(start, start + itemsPerPage)
})

const changePage = (page) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const getCategoryLabel = (value) => {
  const cat = categories.find(c => c.value === value)
  return cat ? cat.label : value
}

const selectCategory = (category) => {
  selectedCategory.value = category
  selectedSubcategories.value = []
  currentPage.value = 1
}

const clearCategory = () => {
  selectedCategory.value = null
  selectedSubcategories.value = []
  fetchServices()
}

const toggleSubcategory = (subcategory) => {
  const index = selectedSubcategories.value.indexOf(subcategory)
  if (index > -1) {
    selectedSubcategories.value.splice(index, 1)
  } else {
    selectedSubcategories.value.push(subcategory)
  }
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

const fetchServices = async () => {
  loading.value = true
  try {
    let url = '/api/market/services/'
    const params = new URLSearchParams()
    
    if (selectedCategory.value && selectedSubcategories.value.length === 0) {
      params.append('categories', selectedCategory.value)
    }
    
    if (selectedSubcategories.value.length > 0) {
      params.append('subcategories', selectedSubcategories.value.join(','))
    }
    
    const res = await axios.get(url, { params })
    const data = res.data.status === 'success' ? res.data.data : (Array.isArray(res.data) ? res.data : (res.data.data || []))
    allServices.value = data
    services.value = data
  } catch (e) { 
    console.error(e) 
  } finally { 
    loading.value = false 
  }
}

const handleSearch = () => {
  const query = searchQuery.value.toLowerCase().trim()
  currentPage.value = 1 
  services.value = query ? allServices.value.filter(s => s.title?.toLowerCase().includes(query) || s.description?.toLowerCase().includes(query)) : allServices.value
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = null
  selectedSubcategories.value = []
  fetchServices()
}

watch(selectedSubcategories, () => {
  fetchServices()
}, { deep: true })

onMounted(() => {
  fetchSubcategories()
  fetchServices()
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}
.glass-chip { background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border: 1px solid rgba(255, 255, 255, 0.2); }
.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
