<template>
  <div class="app">
    <TopNav v-if="!isMobile" />
    <BottomNav v-if="isMobile" />
    <main class="main-content">
      <router-view />
    </main>
    
    <SupportButton v-if="!isChatPage" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue' // Добавили computed
import { useRoute } from 'vue-router' // Добавили useRoute
import TopNav from './components/TopNav.vue'
import BottomNav from './components/BottomNav.vue'
import SupportButton from './components/SupportButton.vue'

const route = useRoute()
const isMobile = ref(false)

// Проверка: начинается ли адрес с /chats
const isChatPage = computed(() => route.path.startsWith('/chats'))

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.main-content {
  max-width: 1200px;
  margin: 140px auto 20px; 
  padding: 0 20px;
}

@media (max-width: 768px) {
  .main-content {
    margin-top: 40px; 
    margin-bottom: 120px;
  }
}
</style>