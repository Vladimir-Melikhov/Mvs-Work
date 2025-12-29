<template>
  <div class="fixed inset-0 bg-black/20 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in">
    <div class="bg-white rounded-[32px] p-8 pr-6 max-w-2xl w-full shadow-2xl relative border border-white/50 max-h-[90vh] overflow-y-auto custom-scrollbar">
      
      <button 
        @click="$emit('close')" 
        class="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 transition-colors flex items-center justify-center font-bold text-xl"
      >
        ×
      </button>

      <div v-if="step === 1">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-12 h-12 rounded-full bg-transparent border-2 border-[#7000ff] flex items-center justify-center text-[#7000ff] text-xl font-bold">
            Ai
          </div>
          <div>
            <h2 class="text-2xl font-bold text-[#1a1a2e]">AI-ассистент заказа</h2>
            <p class="text-sm text-gray-500">Опишите вашу задачу, AI создаст ТЗ</p>
          </div>
        </div>

        <div class="bg-[#7000ff]/5 rounded-2xl p-4 mb-6 border border-[#7000ff]/10">
          <div class="flex items-start gap-3">
            <div class="text-2xl">📋</div>
            <div>
              <div class="font-bold text-[#1a1a2e] mb-1">Услуга: {{ service?.title }}</div>
              <div class="text-sm text-gray-600">Цена: <span class="font-bold text-[#7000ff]">{{ service?.price }}₽</span></div>
            </div>
          </div>
        </div>
        
        <div class="space-y-4">
          
          <div v-if="service?.ai_template" class="bg-[#7000ff]/5 border border-[#7000ff]/20 rounded-xl p-4">
              <div class="text-xs font-bold text-[#7000ff] uppercase tracking-wider mb-2">
                Важное примечание от исполнителя
              </div>
              <p class="text-sm text-[#1a1a2e] font-medium whitespace-pre-line leading-relaxed">
                {{ service.ai_template }}
              </p>
          </div>

          <label class="block">
            <span class="text-sm font-bold text-gray-700 mb-2 block">Опишите вашу задачу</span>
            <textarea 
              v-model="requirements" 
              class="w-full p-4 bg-gray-50 rounded-xl h-48 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/20 focus:border-[#7000ff] transition-all resize-none font-medium text-[#1a1a2e]"
              :placeholder="placeholderText"
            ></textarea>
          </label>

          <div class="bg-blue-50 border border-blue-200 rounded-xl p-3 text-sm text-blue-800">
            <div class="font-bold mb-1">💡 Совет:</div>
            <div>Чем подробнее вы опишете задачу, тем точнее будет техническое задание. Укажите желаемые функции, сроки, стиль, примеры.</div>
          </div>
        </div>

        <button 
          @click="generateTZ" 
          :disabled="!requirements.trim() || loading"
          class="w-full mt-6 bg-[#7000ff] hover:bg-[#5500cc] text-white py-4 rounded-xl font-bold shadow-lg shadow-[#7000ff]/20 hover:shadow-xl hover:scale-[1.01] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
        >
          <span v-if="loading">⏳ Генерируем...</span>
          <span v-else>
            <span class="text-xl">✨</span> Сгенерировать ТЗ с помощью AI
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
        <h3 class="text-xl font-bold text-[#1a1a2e] mb-2">AI анализирует ваш запрос</h3>
        <p class="text-gray-600">Генерируем структурированное техническое задание...</p>
      </div>

      <div v-if="step === 3">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-2xl">
            ✅
          </div>
          <div>
            <h2 class="text-2xl font-bold text-[#1a1a2e]">ТЗ готово!</h2>
            <p class="text-sm text-gray-500">Проверьте и отредактируйте при необходимости</p>
          </div>
        </div>

        <div class="bg-gray-50 border border-gray-200 rounded-2xl p-6 mb-6 max-h-[400px] overflow-y-auto custom-scrollbar">
          <div class="prose prose-sm max-w-none">
            <div v-html="formatMarkdown(generatedTz)" class="text-sm leading-relaxed"></div>
          </div>
        </div>

        <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
          <div class="flex items-start gap-3">
            <div class="text-xl">⚠️</div>
            <div class="text-sm text-amber-800">
              <div class="font-bold mb-1">Важно:</div>
              <div>Внимательно проверьте ТЗ перед подтверждением. После создания заказа изменить условия можно будет только по согласованию с исполнителем.</div>
            </div>
          </div>
        </div>
        
        <div class="flex gap-4">
          <button 
            @click="step = 1" 
            class="flex-1 border-2 border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-bold text-gray-700"
          >
            ← Назад
          </button>
          <button 
            @click="createOrder" 
            :disabled="creating"
            class="flex-1 bg-[#7000ff] hover:bg-[#5500cc] text-white py-3 rounded-xl shadow-lg shadow-[#7000ff]/20 hover:shadow-xl hover:scale-[1.01] transition-all font-bold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="creating">⏳ Создаём заказ...</span>
            <span v-else>🚀 Создать заказ</span>
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
const loading = ref(false)
const creating = ref(false)

const placeholderText = computed(() => {
  if (props.service?.ai_template) {
    return 'Опишите задачу, учитывая примечание выше...'
  }
  return 'Например:\n\nМне нужен сайт для моей кофейни. Хочу:\n- Галерею с фотографиями\n- Меню с ценами\n- Форму обратной связи'
})

const generateTZ = async () => {
  if (!requirements.value.trim()) return
  
  step.value = 2
  loading.value = true
  
  try {
    const res = await axios.post('/api/market/orders/preview/', {
      service_id: props.service.id,
      raw_requirements: requirements.value
    })
    
    if (res.data.status === 'success') {
      generatedTz.value = res.data.data.generated_tz
      step.value = 3
    } else {
      throw new Error('Ошибка генерации')
    }
  } catch (e) {
    console.error('TZ generation error:', e)
    setTimeout(() => {
      generatedTz.value = generateFallbackTZ()
      step.value = 3
    }, 1500)
  } finally {
    loading.value = false
  }
}

const generateFallbackTZ = () => {
  return `# Техническое задание\n\n## 📋 Описание\n${requirements.value}\n\n## 💰 Бюджет\n${props.service.price}₽\n\n---`
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
    await axios.post('/api/market/orders/create/', {
      service_id: props.service.id,
      agreed_tz: generatedTz.value
    })
    
    alert('🎉 Заказ успешно создан!')
    emit('close')
    router.push('/chats')
    
  } catch (e) {
    console.error('Order creation error:', e)
    let errorMsg = 'Ошибка создания заказа.'
    if (e.response && e.response.data) {
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
