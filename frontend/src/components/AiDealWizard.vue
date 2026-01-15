<template>
  <div class="fixed inset-0 bg-black/20 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in">
    <div class="bg-white rounded-[32px] p-6 md:p-8 md:pr-6 max-w-2xl w-full shadow-2xl relative border border-white/50 max-h-[90vh] overflow-y-auto custom-scrollbar">
      
      <button 
        @click="$emit('close')" 
        class="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 transition-colors flex items-center justify-center font-bold text-xl"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div v-if="step === 1">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-12 h-12 rounded-full bg-transparent border-2 border-[#7000ff] flex items-center justify-center text-[#7000ff] text-xl font-bold">
            Ai
          </div>
          <div>
            <h2 class="text-xl md:text-2xl font-bold text-[#1a1a2e]">Оформление заказа</h2>
            <p class="text-sm text-gray-500">Опишите вашу задачу</p>
          </div>
        </div>

        <div class="bg-[#7000ff]/5 rounded-2xl p-4 mb-6 border border-[#7000ff]/10">
          <div class="flex items-start gap-3">
            <div class="text-[#7000ff] mt-1">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-bold text-[#1a1a2e] mb-1 break-words">Услуга: {{ service?.title }}</div>
              <div class="text-sm text-gray-600">Цена: <span class="font-bold text-[#7000ff]">{{ service?.price }}₽</span></div>
            </div>
          </div>
        </div>
        
        <div class="space-y-4">
          
          <div v-if="service?.ai_template" class="bg-[#7000ff]/5 border border-[#7000ff]/20 rounded-xl p-4">
              <div class="text-xs font-bold text-[#7000ff] uppercase tracking-wider mb-2">
                Важное примечание от исполнителя
              </div>
              <p class="text-sm text-[#1a1a2e] font-medium whitespace-pre-line leading-relaxed break-words">
                {{ service.ai_template }}
              </p>
          </div>

          <label class="block">
            <span class="text-sm font-bold text-gray-700 mb-2 block">Опишите вашу задачу</span>
            <textarea 
              v-model="requirements" 
              class="w-full p-3 md:p-4 bg-gray-50 rounded-xl h-48 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/20 focus:border-[#7000ff] transition-all resize-none font-medium text-[#1a1a2e] text-sm md:text-base"
              :placeholder="placeholderText"
            ></textarea>
          </label>

          <label class="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl cursor-pointer hover:bg-blue-100 transition-colors">
            <input 
              type="checkbox" 
              v-model="useAI" 
              class="mt-1 w-5 h-5 text-[#7000ff] rounded border-gray-300 focus:ring-2 focus:ring-[#7000ff]/20"
            >
            <div class="flex-1 min-w-0">
              <div class="font-bold text-[#1a1a2e] mb-1 flex items-center gap-2 flex-wrap">
                <svg class="w-4 h-4 text-[#7000ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Использовать AI для создания ТЗ</span>
              </div>
              <div class="text-xs text-gray-600 break-words">
                Нейросеть структурирует ваше описание в профессиональное техническое задание
              </div>
            </div>
          </label>

          <div v-if="!useAI" class="bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm text-amber-800">
            <div class="font-bold mb-1 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Без AI:
            </div>
            <div>Ваш текст будет отправлен "как есть" без структурирования.</div>
          </div>
        </div>

        <button 
          @click="handleNext" 
          :disabled="!requirements.trim() || loading"
          class="w-full mt-6 bg-[#7000ff] hover:bg-[#5500cc] text-white py-3 md:py-4 rounded-xl font-bold shadow-lg shadow-[#7000ff]/20 hover:shadow-xl hover:scale-[1.01] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2 text-sm md:text-base"
        >
          <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <span v-else-if="useAI" class="flex items-center gap-2 text-white">
             <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Сгенерировать ТЗ с AI
          </span>
          <span v-else class="flex items-center gap-2">
            Далее 
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </span>
        </button>
      </div>

      <div v-if="step === 2" class="text-center py-20">
        <div class="relative w-24 h-24 mx-auto mb-6">
          <div class="absolute inset-0 border-2 border-[#7000ff] rounded-full animate-ping opacity-30"></div>
          <div class="absolute inset-0 bg-transparent border-2 border-[#7000ff] rounded-full flex items-center justify-center text-3xl font-bold text-[#7000ff]">
            Ai
          </div>
        </div>
        <h3 class="text-lg md:text-xl font-bold text-[#1a1a2e] mb-2">AI анализирует ваш запрос</h3>
        <p class="text-sm md:text-base text-gray-600">Генерируем структурированное техническое задание...</p>
      </div>

      <div v-if="step === 3">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-12 h-12 rounded-full bg-green-50 border border-green-100 flex items-center justify-center text-green-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h2 class="text-xl md:text-2xl font-bold text-[#1a1a2e]">ТЗ готово!</h2>
            <p class="text-sm text-gray-500">Проверьте и отредактируйте при необходимости</p>
          </div>
        </div>

        <div class="mb-6">
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-bold text-gray-700">Техническое задание</label>
            <button 
              v-if="!editing"
              @click="editing = true" 
              class="text-xs font-bold text-[#7000ff] hover:underline flex items-center gap-1"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              Редактировать
            </button>
            <button 
              v-else
              @click="editing = false" 
              class="text-xs font-bold text-green-600 hover:underline flex items-center gap-1"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
              Готово
            </button>
          </div>

          <div v-if="!editing" class="bg-gray-50 border border-gray-200 rounded-2xl p-4 md:p-6 max-h-[400px] overflow-y-auto custom-scrollbar">
            <div class="prose prose-sm max-w-none">
              <div v-html="formatMarkdown(editableTz)" class="text-sm leading-relaxed text-[#1a1a2e] break-words"></div>
            </div>
          </div>

          <textarea 
            v-else
            v-model="editableTz"
            rows="15"
            class="w-full p-3 md:p-4 bg-white border border-[#7000ff] rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-[#7000ff]/20 text-sm font-mono leading-relaxed"
          ></textarea>
        </div>

        <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
          <div class="flex items-start gap-3">
            <div class="text-amber-600">
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="text-sm text-amber-800 flex-1 min-w-0">
              <div class="font-bold mb-1">Важно:</div>
              <div class="break-words">Внимательно проверьте ТЗ перед подтверждением. После оплаты изменить условия будет нельзя.</div>
            </div>
          </div>
        </div>
        
        <div class="flex flex-col sm:flex-row gap-3 sm:gap-4">
          <button 
            @click="step = 1; editing = false" 
            class="w-full sm:flex-1 border-2 border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-bold text-gray-700 flex items-center justify-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Назад
          </button>
          <button 
            @click="createOrder" 
            :disabled="creating"
            class="w-full sm:flex-1 bg-[#7000ff] hover:bg-[#5500cc] text-white py-3 rounded-xl shadow-lg shadow-[#7000ff]/20 hover:shadow-xl hover:scale-[1.01] transition-all font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span v-if="creating" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span v-else class="flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Создать заказ
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  service: Object
})

const emit = defineEmits(['close'])

const step = ref(1)
const requirements = ref('')
const generatedTz = ref('')
const editableTz = ref('')
const editing = ref(false)
const useAI = ref(true)
const loading = ref(false)
const creating = ref(false)

const placeholderText = computed(() => {
  if (props.service?.ai_template) {
    return 'Опишите задачу, учитывая примечание выше...'
  }
  return 'Например:\n\nМне нужен сайт для моей кофейни. Хочу:\n- Галерею с фотографиями\n- Меню с ценами\n- Форму обратной связи'
})

const handleNext = async () => {
  if (!requirements.value.trim()) return
  
  if (useAI.value) {
    await generateTZ()
  } else {
    editableTz.value = requirements.value
    step.value = 3
  }
}

const generateTZ = async () => {
  step.value = 2
  loading.value = true
  
  try {
    const res = await axios.post('/api/market/deals/generate-tz/', {
      service_id: props.service.id,
      raw_requirements: requirements.value
    })
    
    if (res.data.status === 'success') {
      generatedTz.value = res.data.data.generated_tz
      editableTz.value = res.data.data.generated_tz
      step.value = 3
    } else {
      throw new Error('Ошибка генерации')
    }
  } catch (e) {
    console.error('TZ generation error:', e)
    editableTz.value = generateFallbackTZ()
    step.value = 3
  } finally {
    loading.value = false
  }
}

const generateFallbackTZ = () => {
  return `# Техническое задание\n\n## Описание\n${requirements.value}\n\n## Бюджет\n${props.service.price}₽\n\n---`
}

const formatMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2 text-[#1a1a2e]">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-6 mb-3 text-[#1a1a2e]">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-6 mb-4 text-[#1a1a2e]">$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-bold text-[#1a1a2e]">$1</strong>')
    .replace(/^\- (.*$)/gim, '<li class="ml-4 my-1">• $1</li>')
    .replace(/\n\n/g, '</p><p class="my-2">')
    .replace(/^(.*)$/gim, '<p class="my-2">$1</p>')
}

const createOrder = async () => {
  creating.value = true
  
  try {
    const chatRes = await axios.post('/api/chat/rooms/create_room/', {
      user2_id: props.service.owner_id
    })
    
    const chatRoomId = chatRes.data.data.id

    await axios.post('/api/market/deals/create/', {
      chat_room_id: chatRoomId,
      title: props.service.title,
      description: editableTz.value,
      price: props.service.price
    })
    
    emit('close')
    router.push(`/chats/${chatRoomId}`)
    
  } catch (e) {
    console.error('Order creation error:', e)
    let errorMsg = 'Ошибка создания заказа.'
    
    if (e.response?.data?.error) {
      if (typeof e.response.data.error === 'string') {
        errorMsg = e.response.data.error
      } else if (typeof e.response.data.error === 'object') {
        errorMsg = JSON.stringify(e.response.data.error)
      }
    }
    
    alert('❌ ' + errorMsg)
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
  margin-block: 20px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #7000ff;
  border-radius: 10px;
  border: 1px solid transparent;
  background-clip: content-box;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #5500cc;
  border: 1px solid transparent;
  background-clip: content-box;
}
</style>
