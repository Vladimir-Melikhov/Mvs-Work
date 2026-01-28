<!-- frontend/src/components/TelegramNotificationBanner.vue -->
<template>
    <div 
      v-if="showBanner"
      class="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-3 py-1.5 rounded-xl shadow-md"
    >
      <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
      </svg>
      
      <span class="text-xs font-semibold whitespace-nowrap">Telegram</span>
      
      <button
        @click="openModal"
        class="px-2 py-0.5 bg-white/20 hover:bg-white/30 rounded-lg text-xs font-bold transition-all whitespace-nowrap"
      >
        Подключить
      </button>
      
      <button
        @click="closeBanner"
        class="w-5 h-5 flex items-center justify-center hover:bg-white/20 rounded-full transition-all shrink-0 ml-1"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <Teleport to="body">
      <TelegramLinkModal 
        v-if="showModal"
        @close="showModal = false"
        @connected="handleConnected"
      />
    </Teleport>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  import TelegramLinkModal from './TelegramLinkModal.vue'
  
  const auth = useAuthStore()
  const showModal = ref(false)
  const isClosed = ref(false)
  const bannerDismissedKey = 'telegram_banner_dismissed'
  
  const showBanner = computed(() => {
    if (isClosed.value) return false
    
    // Проверяем localStorage - если пользователь закрыл баннер
    if (localStorage.getItem(bannerDismissedKey) === 'true') {
      return false
    }
    
    // Показываем только если Telegram НЕ подключен
    if (!auth.user?.profile) return false
    
    return !auth.user.profile.telegram_notifications_enabled
  })
  
  const openModal = () => {
    showModal.value = true
  }
  
  const closeBanner = () => {
    isClosed.value = true
    localStorage.setItem(bannerDismissedKey, 'true')
  }
  
  const handleConnected = async () => {
    showModal.value = false
    
    // Обновляем профиль, чтобы получить актуальный статус
    await auth.fetchProfile()
    
    // После успешного подключения баннер исчезнет автоматически
    // так как telegram_notifications_enabled станет true
  }
  
  // При монтировании проверяем актуальный статус
  onMounted(async () => {
    if (auth.user) {
      await auth.fetchProfile()
    }
  })
  </script>
