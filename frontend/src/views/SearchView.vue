<template>
  <div class="min-h-screen pt-4 pb-20">
    <div class="text-center mb-8 md:mb-12 px-4">
      <h1 class="text-2xl md:text-4xl font-bold text-[#1a1a2e] mb-4 md:mb-6 tracking-tight leading-tight">
        Поиск идеального<br class="md:hidden"> исполнителя + AI
      </h1>
      
      <div class="max-w-2xl mx-auto relative">
        <div class="glass p-2 rounded-full flex items-center shadow-xl transition-all focus-within:bg-white/20 focus-within:border-white/40 focus-within:shadow-2xl">
           <span class="pl-4 md:pl-6 text-xl opacity-50">🔍</span>
           <input 
             v-model="searchQuery"
             @keydown.enter="handleSearch"
             placeholder="Что нужно сделать?" 
             class="w-full bg-transparent border-none outline-none text-base md:text-lg p-3 md:p-4 placeholder-gray-500 text-[#1a1a2e] font-medium"
           >
           <button 
             @click="handleSearch"
             class="bg-[#1a1a2e] text-white px-6 md:px-8 py-3 rounded-full font-bold hover:bg-[#7000ff] transition-colors shadow-md mr-1 text-sm md:text-base whitespace-nowrap"
           >
             Найти
           </button>
        </div>
      </div>
      
      <div class="flex justify-center gap-2 mt-6 md:mt-8 flex-wrap px-2">
         <button 
           v-for="cat in categories" 
           :key="cat.value" 
           @click="toggleCategory(cat.value)"
           class="px-3 md:px-5 py-2 rounded-full text-xs md:text-sm font-bold transition-all border"
           :class="selectedCategories.includes(cat.value) 
             ? 'bg-[#7000ff] text-white border-[#7000ff] shadow-lg' 
             : 'glass-chip text-gray-600 hover:bg-white/30 hover:text-[#1a1a2e] border-white/20'"
         >
           {{ cat.label }}
         </button>
         <button 
           v-if="selectedCategories.length > 0"
           @click="clearFilters"
           class="px-3 md:px-5 py-2 rounded-full glass-chip text-xs md:text-sm font-bold text-red-500 hover:bg-red-50 transition-all border border-red-200"
         >
           ✕ Сбросить
         </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-20">
      <div class="inline-block w-12 h-12 border-4 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
      <p class="mt-4 text-gray-500">Загрузка...</p>
    </div>

    <div v-else-if="paginatedServices.length > 0">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 animate-fade-in px-4">
        <div 
          v-for="service in paginatedServices" 
          :key="service.id" 
          class="glass rounded-[32px] overflow-hidden hover:bg-white/20 transition-all cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1"
          @click="$router.push(`/services/${service.id}`)"
        >
          <div v-if="service.images && service.images.length > 0" class="relative aspect-video overflow-hidden">
            <img 
              :src="service.images[0].image_url" 
              class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              alt="Service preview"
            >
            <div v-if="service.images.length > 1" class="absolute bottom-3 right-3 px-2 py-1 rounded-lg bg-black/40 backdrop-blur-md text-white text-[10px] font-bold border border-white/20">
              +{{ service.images.length - 1 }} фото
            </div>
          </div>
          <div v-else class="aspect-video bg-gray-100 flex items-center justify-center text-gray-300">
             <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>

          <div class="p-4 md:p-6 flex flex-col flex-1">
            <div class="flex items-center gap-3 mb-4">
              <UserAvatar :avatar-url="service.owner_avatar" :name="service.owner_name || 'Специалист'" size="md" class="border border-white/30 shadow-sm" />
              <div class="flex-1 min-w-0">
                 <div class="text-sm font-bold text-[#1a1a2e] truncate">{{ service.owner_name || 'Специалист' }}</div>
                 <div class="text-[10px] text-gray-500 font-bold uppercase tracking-wider">{{ service.category || 'Услуга' }}</div>
              </div>
              <div class="text-[#7000ff] font-bold text-base md:text-lg shrink-0">{{ service.price }}₽</div>
            </div>

            <h3 class="text-lg md:text-xl font-bold text-[#1a1a2e] mb-2 leading-tight group-hover:text-[#7000ff] transition-colors line-clamp-2 break-words">{{ service.title }}</h3>
            <p class="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-2 flex-1 break-words">{{ service.description }}</p>

            <div class="flex items-center justify-between mt-auto pt-4 border-t border-white/10">
               <div class="flex flex-wrap gap-2">
                  <span v-for="tag in service.tags?.slice(0,2)" :key="tag" class="px-3 py-1 rounded-lg bg-white/20 text-xs font-bold text-gray-600 border border-white/20 break-words">#{{ tag }}</span>
               </div>
               
               <div v-if="service.owner_rating > 0" class="flex items-center gap-1.5 bg-[#7000ff]/5 px-3 py-1.5 rounded-xl border border-[#7000ff]/10">
                 <span class="text-[#7000ff] text-xs font-black">★</span>
                 <span class="text-[#7000ff] text-[13px] font-black tracking-tight">
                   {{ Number(service.owner_rating).toFixed(1) }}
                 </span>
               </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="flex justify-center items-center gap-2 mt-12 mb-8">
        <button 
          @click="changePage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="w-10 h-10 rounded-full glass flex items-center justify-center transition-all hover:bg-[#7000ff] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
        >
          ←
        </button>
        
        <div class="flex gap-2">
          <button 
            v-for="page in totalPages" 
            :key="page"
            @click="changePage(page)"
            class="w-10 h-10 rounded-full font-bold text-sm transition-all border"
            :class="currentPage === page 
              ? 'bg-[#1a1a2e] text-white border-[#1a1a2e] shadow-lg scale-110' 
              : 'glass hover:bg-white/40 text-[#1a1a2e] border-white/20'"
          >
            {{ page }}
          </button>
        </div>

        <button 
          @click="changePage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="w-10 h-10 rounded-full glass flex items-center justify-center transition-all hover:bg-[#7000ff] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
        >
          →
        </button>
      </div>
    </div>
    
    <div v-else class="text-center py-20 opacity-50 px-4">
       <div class="text-6xl mb-4">🌪️</div>
       <p class="font-bold text-[#1a1a2e] mb-2">Услуги не найдены</p>
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
const selectedCategories = ref([])

const currentPage = ref(1)
const itemsPerPage = 6

const categories = [
  { label: 'Дизайн', value: 'design' },
  { label: 'Разработка', value: 'development' },
  { label: 'Тексты', value: 'copywriting' },
  { label: 'Маркетинг', value: 'marketing' },
]

const totalPages = computed(() => Math.ceil(services.value.length / itemsPerPage))

const paginatedServices = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return services.value.slice(start, end)
})

const changePage = (page) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchServices = async () => {
  loading.value = true
  try {
    let url = '/api/market/services/'
    const params = new URLSearchParams()
    if (selectedCategories.value.length > 0) {
      params.append('categories', selectedCategories.value.join(','))
    }
    const res = await axios.get(url, { params })
    
    const data = res.data.status === 'success' ? res.data.data : (Array.isArray(res.data) ? res.data : (res.data.data || []))
    allServices.value = data
    services.value = data
    currentPage.value = 1 
  } catch (e) {
    console.error("Ошибка:", e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  const query = searchQuery.value.toLowerCase().trim()
  currentPage.value = 1 
  if (!query) {
    services.value = allServices.value
    return
  }
  services.value = allServices.value.filter(service => (
    service.title?.toLowerCase().includes(query) ||
    service.description?.toLowerCase().includes(query) ||
    service.tags?.some(tag => tag.toLowerCase().includes(query)) ||
    service.owner_name?.toLowerCase().includes(query)
  ))
}

const toggleCategory = (category) => {
  const index = selectedCategories.value.indexOf(category)
  if (index > -1) selectedCategories.value.splice(index, 1)
  else selectedCategories.value.push(category)
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedCategories.value = []
  fetchServices()
}

watch(selectedCategories, () => fetchServices(), { deep: true })

onMounted(() => fetchServices())
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.191);
  backdrop-filter: blur(9px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.125);
}
.glass-chip { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(120px); }
.animate-fade-in { animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>