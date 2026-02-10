<!-- frontend/src/App.vue -->
<template>
  <div class="app">
    <TopNav v-if="!isMobile" />
    <BottomNav v-if="isMobile" />
    <main class="main-content" :class="{ 'onboarding-page': isOnboardingPage }">
      <router-view />
    </main>
    
    <SupportButton v-if="!isChatPage" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/authStore'
import TopNav from './components/TopNav.vue'
import BottomNav from './components/BottomNav.vue'
import SupportButton from './components/SupportButton.vue'

const route = useRoute()
const authStore = useAuthStore()
const isMobile = ref(false)

const isChatPage = computed(() => route.path.startsWith('/chats'))
const isOnboardingPage = computed(() => route.path === '/onboarding')

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  await authStore.initAuth()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
/* ✅ ЗАДАЧА 4: Уменьшение отступа сверху для десктопа и планшетов */
.main-content {
  max-width: 1200px;
  margin: 110px auto 20px; 
  padding: 0 8px;
}

.main-content.onboarding-page {
  max-width: 100%;
  margin-top: 80px; 
  margin-bottom: 20px;
  padding: 0;
  background: transparent;
}

@media (max-width: 768px) {
  .main-content {
    margin-top: 20px; 
    margin-bottom: 100px;
    padding: 0 8px;
  }
  
  .main-content.onboarding-page {
    margin-top: 20px;
    margin-bottom: 100px;
    padding: 0;
  }
}
</style>