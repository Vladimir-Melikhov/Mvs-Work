<template>
  <div class="app">
    <TopNav v-if="!isMobile" />
    <BottomNav v-if="isMobile" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import TopNav from './components/TopNav.vue'
import BottomNav from './components/BottomNav.vue'

const isMobile = ref(false)

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
  margin: 90px auto 20px;
  padding: 0 20px;
}

@media (max-width: 768px) {
  .main-content {
    margin-top: 20px;
    margin-bottom: 100px;
  }
}
</style>