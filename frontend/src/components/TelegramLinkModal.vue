<template>
    <div class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[200] flex items-center justify-center p-4 animate-fade-in">
      <div class="bg-white rounded-[32px] p-8 max-w-md w-full shadow-2xl relative border border-white/50">
        
        <button 
          @click="$emit('close')" 
          class="absolute top-6 right-6 w-8 h-8 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-900 transition-all flex items-center justify-center"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
  
        <div v-if="step === 'loading'" class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mx-auto mb-6">
            <svg class="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Генерируем ссылку...</h3>
          <p class="text-sm text-gray-500">Подождите немного</p>
        </div>
  
        <div v-else-if="step === 'link'" class="text-center">
          <div class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mx-auto mb-6">
            <svg class="w-8 h-8 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
            </svg>
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-2">Подключите Telegram</h3>
          <p class="text-sm text-gray-500 mb-6">Нажмите на кнопку ниже чтобы активировать уведомления</p>
          
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
            <div class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2">Инструкция:</div>
            <ol class="text-sm text-blue-900 text-left space-y-2">
              <li class="flex items-start gap-2">
                <span class="font-bold shrink-0">1.</span>
                <span>Нажмите кнопку "Открыть Telegram"</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="font-bold shrink-0">2.</span>
                <span>Нажмите "START" в боте</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="font-bold shrink-0">3.</span>
                <span>Готово! Уведомления активированы</span>
              </li>
            </ol>
          </div>
          
          <a 
            :href="telegramLink" 
            target="_blank"
            class="block w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-4 rounded-xl font-bold shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all mb-4"
          >
            Открыть Telegram
          </a>
          
          <p class="text-xs text-gray-400">Ссылка действительна 10 минут</p>
        </div>
  
        <div v-else-if="step === 'error'" class="text-center">
          <div class="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-6">
            <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-2">Ошибка</h3>
          <p class="text-sm text-gray-500 mb-6">{{ errorMessage }}</p>
          
          <button 
            @click="generateLink"
            class="w-full bg-gray-900 text-white py-3 rounded-xl font-bold hover:bg-gray-800 transition-all"
          >
            Попробовать снова
          </button>
        </div>
  
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  
  const emit = defineEmits(['close', 'connected'])
  
  const step = ref('loading') // 'loading', 'link', 'error'
  const telegramLink = ref('')
  const errorMessage = ref('')
  
  const generateLink = async () => {
    step.value = 'loading'
    
    try {
      const response = await axios.post('/api/auth/telegram/generate-link/')
      
      if (response.data.status === 'success') {
        telegramLink.value = response.data.data.link
        step.value = 'link'
        
        // Через 10 минут ссылка истечет
        setTimeout(() => {
          if (step.value === 'link') {
            errorMessage.value = 'Ссылка истекла. Сгенерируйте новую.'
            step.value = 'error'
          }
        }, 10 * 60 * 1000)
      } else {
        throw new Error(response.data.error || 'Неизвестная ошибка')
      }
    } catch (error) {
      console.error('Ошибка генерации ссылки:', error)
      errorMessage.value = error.response?.data?.error || 'Не удалось сгенерировать ссылку'
      step.value = 'error'
    }
  }
  
  onMounted(() => {
    generateLink()
  })
  </script>
  
  <style scoped>
  .animate-fade-in {
    animation: fadeIn 0.2s ease-out;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }
  </style>