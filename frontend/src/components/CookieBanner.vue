<template>
  <Transition name="cookie-slide">
    <div
      v-if="showBanner"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[9998] w-[calc(100%-32px)] max-w-2xl"
    >
      <div class="glass rounded-[24px] px-5 py-4 flex items-center gap-4 shadow-2xl border border-white/40 flex-wrap md:flex-nowrap">
        
        <div class="text-2xl shrink-0">🍪</div>
        
        <p class="text-xs text-gray-600 flex-1 leading-relaxed min-w-0">
          Мы используем файлы cookie для корректной работы сайта и аналитики.
          Продолжая использовать сайт, вы соглашаетесь с нашей
          <a
            href="/docs/privacy-policy.pdf"
            target="_blank"
            rel="noopener noreferrer"
            class="text-[#7000ff] hover:underline font-semibold"
          >политикой конфиденциальности</a>
        </p>

        <div class="flex items-center gap-2 shrink-0 w-full md:w-auto">
          <button
            @click="decline"
            class="flex-1 md:flex-none px-4 py-2 rounded-xl text-xs font-bold text-gray-500 hover:bg-black/5 transition-colors border border-gray-200"
          >
            Отклонить
          </button>
          <button
            @click="accept"
            class="flex-1 md:flex-none px-5 py-2 rounded-xl text-xs font-bold text-white bg-[#7000ff] hover:bg-[#5500cc] transition-colors shadow-lg shadow-[#7000ff]/20"
          >
            Принять
          </button>
        </div>

      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const COOKIE_KEY = 'cookie_consent'
const showBanner = ref(false)

onMounted(() => {
  const saved = localStorage.getItem(COOKIE_KEY)
  if (!saved) {
    setTimeout(() => {
      showBanner.value = true
    }, 1000)
  }
})

const accept = () => {
  localStorage.setItem(COOKIE_KEY, 'accepted')
  showBanner.value = false
}

const decline = () => {
  localStorage.setItem(COOKIE_KEY, 'declined')
  showBanner.value = false
}
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.cookie-slide-enter-active,
.cookie-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.cookie-slide-enter-from,
.cookie-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>