<template>
    <div class="animate-fade-in pb-20 pt-4">
      
      <div class="glass p-8 rounded-[40px] relative overflow-hidden mb-8 group">
        <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-[#7000ff]/10 to-[#00c6ff]/10 blur-2xl opacity-60"></div>
        
        <button @click="toggleEdit" class="absolute top-8 right-8 z-10 text-gray-400 hover:text-[#1a1a2e] text-sm font-bold transition-colors">
          {{ isEditing ? 'Отмена' : 'Редактировать' }}
        </button>
  
        <div class="relative flex flex-col md:flex-row items-center gap-8 mt-4">
          
          <div class="w-32 h-32 rounded-full p-1.5 shadow-xl border border-white/20 relative">
             <img v-if="user?.profile?.avatar" :src="user.profile.avatar" class="w-full h-full rounded-full object-cover">
             <div v-else class="w-full h-full rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] flex items-center justify-center text-white text-4xl font-bold">
               {{ userInitials }}
             </div>
             
             <div v-if="isEditing" class="absolute -bottom-6 left-1/2 -translate-x-1/2 w-40">
               <input v-model="editForm.avatar" placeholder="URL аватара" class="text-[10px] w-full p-1.5 bg-white/20 backdrop-blur-md border border-white/30 rounded-lg text-center outline-none shadow-md text-[#1a1a2e] placeholder-gray-500">
             </div>
          </div>
  
          <div class="text-center md:text-left flex-1 space-y-1">
            <div v-if="isEditing" class="flex flex-col items-center md:items-start gap-3">
               <div class="flex gap-4 mb-2" v-if="!isWorker">
                  <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500 cursor-pointer hover:text-[#1a1a2e]">
                    <input type="radio" :value="false" v-model="isCompanyEdit" class="hidden"> Человек
                  </label>
                  <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500 cursor-pointer hover:text-[#1a1a2e]">
                    <input type="radio" :value="true" v-model="isCompanyEdit" class="hidden"> Компания
                  </label>
               </div>
  
               <input 
                 v-if="isCompanyEdit && !isWorker" 
                 v-model="editForm.company_name" 
                 class="text-4xl font-bold text-[#1a1a2e] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all"
                 placeholder="Название компании"
               >
               <input 
                 v-else 
                 v-model="editForm.full_name" 
                 class="text-4xl font-bold text-[#1a1a2e] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all"
                 placeholder="Ваше имя"
               >
               
               <input 
                 v-if="isWorker" 
                 v-model="editForm.headline" 
                 placeholder="Профессия / Заголовок" 
                 class="text-sm text-[#7000ff] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all font-medium"
               >
               <input 
                 v-else-if="isCompanyEdit" 
                 v-model="editForm.company_website" 
                 placeholder="Ссылка на сайт" 
                 class="text-sm text-[#7000ff] bg-transparent border-b border-transparent hover:border-white/30 focus:border-[#7000ff] outline-none w-full text-center md:text-left transition-all font-medium"
               >
            </div>
  
            <div v-else>
              <div class="inline-block px-3 py-1 rounded-full bg-white/20 border border-white/20 text-[#1a1a2e] text-[10px] font-bold uppercase tracking-wider mb-3 backdrop-blur-sm">
                {{ isWorker ? (user?.profile?.headline || 'Фрилансер') : 'Заказчик' }}
              </div>
              
              <h1 class="text-4xl font-bold text-[#1a1a2e] tracking-tight">
                {{ user?.profile?.company_name || user?.profile?.full_name || user?.email }}
              </h1>
              
              <a v-if="user?.profile?.company_website" :href="user.profile.company_website" target="_blank" class="text-sm text-gray-500 hover:text-[#7000ff] block mt-1 transition-colors">
                {{ user.profile.company_website.replace('https://', '') }}
              </a>
            </div>
          </div>
  
          <div class="bg-white/10 backdrop-blur-md p-6 rounded-3xl border border-white/20 text-center min-w-[180px] shadow-sm">
            <div class="text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-1">Баланс</div>
            <div class="text-3xl font-bold text-[#1a1a2e]">{{ user?.wallet?.balance || '0.00' }}₽</div>
            <button class="mt-2 text-[10px] font-bold text-[#7000ff] hover:text-[#1a1a2e] transition-colors border border-[#7000ff]/20 px-3 py-1 rounded-full hover:bg-white/20">Пополнить</button>
          </div>
        </div>
        
        <div v-if="isEditing" class="mt-8 flex justify-end animate-fade-in">
           <button @click="saveProfile" class="bg-[#1a1a2e] text-white px-8 py-3 rounded-2xl font-bold shadow-lg shadow-[#1a1a2e]/10 hover:scale-105 transition-transform border border-white/10">
              Сохранить
           </button>
        </div>
      </div>
  
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass p-8 rounded-[32px]">
          <h3 class="text-lg font-bold text-[#1a1a2e] mb-4 flex items-center gap-2">О себе</h3>
          <textarea 
            v-if="isEditing" 
            v-model="editForm.bio" 
            rows="5" 
            class="w-full p-4 bg-white/20 rounded-2xl border border-white/20 outline-none focus:bg-white/30 resize-none text-sm transition-all shadow-inner"
            placeholder="Расскажите о себе..."
          ></textarea>
          <p v-else class="text-gray-600 leading-relaxed whitespace-pre-wrap">{{ user?.profile?.bio || 'Информация не заполнена.' }}</p>
        </div>
  
        <div v-if="isWorker" class="glass p-8 rounded-[32px]">
          <h3 class="text-lg font-bold text-[#1a1a2e] mb-4">Навыки</h3>
          
          <div v-if="isEditing" class="space-y-4">
             <div class="flex flex-wrap gap-2">
                <span v-for="(skill, idx) in editForm.skills" :key="idx" class="px-3 py-1.5 rounded-xl bg-white/30 border border-white/30 flex items-center gap-2 text-sm font-medium text-[#1a1a2e]">
                  {{ skill }} <button @click="editForm.skills.splice(idx,1)" class="text-red-500/70 hover:text-red-500 font-bold">×</button>
                </span>
             </div>
             <input 
                v-model="tempSkill" 
                @keydown.enter.prevent="addSkill" 
                placeholder="+ Добавить навык" 
                class="w-full p-4 bg-white/20 rounded-2xl border border-white/20 outline-none text-sm focus:bg-white/30 transition-all shadow-inner placeholder-gray-500"
              >
          </div>
  
          <div v-else class="flex flex-wrap gap-2">
            <span v-for="skill in user?.profile?.skills" :key="skill" class="px-4 py-2 rounded-xl bg-white/30 border border-white/40 text-[#1a1a2e] text-sm font-semibold shadow-sm backdrop-blur-sm">
              {{ skill }}
            </span>
          </div>
        </div>
      </div>
  
      <div v-if="isWorker" class="mt-8 animate-fade-in">
        <div class="flex items-center justify-between mb-6 px-2">
           <h3 class="text-xl font-bold text-[#1a1a2e]">Активные услуги</h3>
           <router-link to="/create-service" class="text-xs font-bold text-[#7000ff] hover:underline bg-white/20 px-3 py-1 rounded-full border border-white/20">
             + Создать новую
           </router-link>
        </div>
  
        <div v-if="loadingServices" class="text-center py-10 opacity-50">
          Загрузка...
        </div>
  
        <div v-else-if="myServices.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div 
            v-for="service in myServices" 
            :key="service.id" 
            class="glass rounded-[32px] p-6 cursor-pointer group flex flex-col h-full border border-white/20 hover:border-white/40 hover:-translate-y-1 transition-all"
            @click="$router.push(`/services/${service.id}`)" 
          >
            <div class="flex items-center gap-3 mb-4">
               <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-[10px] font-bold border border-white/30 overflow-hidden">
                 <img v-if="service.owner_avatar" :src="service.owner_avatar" class="w-full h-full object-cover">
                 <span v-else>Я</span>
               </div>
               <div class="flex-1 min-w-0">
                  <div class="text-xs font-bold text-gray-400 uppercase">Моя услуга</div>
               </div>
               <div class="text-[#7000ff] font-bold text-lg">{{ service.price }}₽</div>
            </div>
  
            <h3 class="text-lg font-bold text-[#1a1a2e] mb-2 leading-tight line-clamp-2">
              {{ service.title }}
            </h3>
            <p class="text-gray-600 text-xs leading-relaxed mb-4 line-clamp-3 flex-1">
              {{ service.description }}
            </p>
  
            <div class="flex flex-wrap gap-2 mt-auto pt-4 border-t border-white/10">
               <span v-for="tag in service.tags?.slice(0,2)" :key="tag" class="px-2 py-1 rounded-lg bg-white/20 text-[10px] font-bold text-gray-600 border border-white/20">
                 #{{ tag }}
               </span>
            </div>
          </div>
        </div>
  
        <div v-else class="glass p-8 rounded-[32px] text-center border border-white/20 opacity-70">
          <p class="font-bold text-[#1a1a2e] mb-2">Услуг пока нет</p>
          <router-link to="/create-service" class="text-sm text-[#7000ff] hover:underline">Начать продавать свои навыки &rarr;</router-link>
        </div>
      </div>
      <button 
        @click="handleLogout" 
        class="mt-12 mx-auto block text-gray-400 hover:text-red-500 text-sm font-bold transition-colors opacity-60 hover:opacity-100"
      >
        Выйти
      </button>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  import { useRouter } from 'vue-router'
  import axios from 'axios'
  
  const auth = useAuthStore()
  const router = useRouter()
  const user = computed(() => auth.user)
  const isWorker = computed(() => user.value?.role === 'worker')
  
  const isEditing = ref(false)
  const isCompanyEdit = ref(false)
  const tempSkill = ref('')
  const editForm = ref({})
  
  const myServices = ref([])
  const loadingServices = ref(false)
  
  const userInitials = computed(() => user.value?.email?.substring(0, 2).toUpperCase() || 'ME')
  
  const toggleEdit = () => {
    if (!isEditing.value) {
      editForm.value = JSON.parse(JSON.stringify(user.value.profile || {}))
      if (!editForm.value.skills) editForm.value.skills = []
      isCompanyEdit.value = !!editForm.value.company_name
    }
    isEditing.value = !isEditing.value
  }
  
  const addSkill = () => {
    if (tempSkill.value.trim()) {
      editForm.value.skills.push(tempSkill.value.trim())
      tempSkill.value = ''
    }
  }
  
  const saveProfile = async () => {
    if (isCompanyEdit.value && !isWorker.value) {
        editForm.value.full_name = null
    } else {
        editForm.value.company_name = null
        if (!isWorker.value) editForm.value.company_website = null
    }
    const res = await auth.updateProfile(editForm.value)
    if (res.success) isEditing.value = false
    else alert("Ошибка сохранения.")
  }
  
  const fetchMyServices = async () => {
    if (!isWorker.value) return
    loadingServices.value = true
    try {
      const res = await axios.get(`/api/market/services/?owner_id=${auth.user.id}`)
      if (res.data.status === 'success') {
         myServices.value = res.data.data
      } else if (Array.isArray(res.data)) {
         myServices.value = res.data
      }
    } catch (e) {
      console.error("Failed to fetch my services", e)
    } finally {
      loadingServices.value = false
    }
  }
  
  const handleLogout = () => {
    auth.logout()
    router.push('/login')
  }
  
  onMounted(async () => { 
    await auth.fetchProfile() 
    fetchMyServices()
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