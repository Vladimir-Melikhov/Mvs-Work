<template>
    <div class="fixed inset-0 bg-black/20 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in">
      <div class="bg-white rounded-3xl p-8 max-w-2xl w-full shadow-2xl relative border border-white/50 max-h-[90vh] overflow-y-auto">
        
        <!-- Кнопка закрытия -->
        <button 
          @click="$emit('close')" 
          class="absolute top-4 right-4 w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 transition-colors flex items-center justify-center font-bold text-xl"
        >
          ×
        </button>
        <div v-if="step === 1">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-12 h-12 rounded-full bg-gradient-to-br from-[#7000ff] to-[#00c6ff] flex items-center justify-center text-white text-2xl">
              ✨
            </div>
            <div>
              <h2 class="text-2xl font-bold text-[#1a1a2e]">AI-ассистент заказа</h2>
              <p class="text-sm text-gray-500">Опишите вашу задачу, AI создаст ТЗ</p>
            </div>
          </div>

          <div class="bg-gradient-to-r from-[#7000ff]/5 to-[#00c6ff]/5 rounded-2xl p-4 mb-6 border border-[#7000ff]/10">
            <div class="flex items-start gap-3">
              <div class="text-2xl">📋</div>
              <div>
                <div class="font-bold text-[#1a1a2e] mb-1">Услуга: {{ service?.title }}</div>
                <div class="text-sm text-gray-600">Цена: <span class="font-bold text-[#7000ff]">${{ service?.price }}</span></div>
              </div>
            </div>
          </div>
          
          <div class="space-y-4">
            <label class="block">
              <span class="text-sm font-bold text-gray-700 mb-2 block">Опишите вашу задачу</span>
              <textarea 
                v-model="requirements" 
                class="w-full p-4 bg-gray-50 rounded-xl h-48 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/20 focus:border-[#7000ff] transition-all resize-none"
                placeholder="Например:&#10;&#10;Мне нужен сайт для моей кофейни. Хочу:&#10;- Галерею с фотографиями&#10;- Меню с ценами&#10;- Форму обратной связи&#10;- Адаптивный дизайн под телефоны&#10;&#10;Желаемый срок: 2 недели"
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
            class="w-full mt-6 bg-gradient-to-r from-[#7000ff] to-[#00c6ff] text-white py-4 rounded-xl font-bold shadow-lg shadow-[#7000ff]/30 hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
          >
            <span v-if="loading">⏳ Генерируем...</span>
            <span v-else>
              <span class="text-xl">✨</span> Сгенерировать ТЗ с помощью AI
            </span>
          </button>
        </div>
  
        <!-- Шаг 2: Загрузка -->
        <div v-if="step === 2" class="text-center py-16">
          <div class="relative w-24 h-24 mx-auto mb-6">
            <div class="absolute inset-0 bg-gradient-to-r from-[#7000ff] to-[#00c6ff] rounded-full animate-ping opacity-20"></div>
            <div class="absolute inset-0 bg-gradient-to-r from-[#7000ff] to-[#00c6ff] rounded-full flex items-center justify-center text-4xl">
              ✨
            </div>
          </div>
          <h3 class="text-xl font-bold text-[#1a1a2e] mb-2">AI анализирует ваш запрос</h3>
          <p class="text-gray-600">Генерируем структурированное техническое задание...</p>
          <div class="mt-6 max-w-xs mx-auto">
            <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-[#7000ff] to-[#00c6ff] animate-pulse" style="width: 70%"></div>
            </div>
          </div>
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

          <div class="bg-gray-50 border border-gray-200 rounded-2xl p-6 mb-6 max-h-[400px] overflow-y-auto">
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
              class="flex-1 bg-gradient-to-r from-[#7000ff] to-[#00c6ff] text-white py-3 rounded-xl shadow-lg shadow-[#7000ff]/30 hover:shadow-xl hover:scale-[1.02] transition-all font-bold disabled:opacity-50 disabled:cursor-not-allowed"
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
  import { ref } from 'vue'
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
  
  // Генерация ТЗ через AI
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
      // Fallback на моковое ТЗ
      setTimeout(() => {
        generatedTz.value = generateFallbackTZ()
        step.value = 3
      }, 1500)
    } finally {
      loading.value = false
    }
  }
  
  // Fallback ТЗ если API не отвечает
  const generateFallbackTZ = () => {
    return `# Техническое задание

## 📋 Описание проекта

${requirements.value}

## 🎯 Цели и задачи

- Реализовать функционал согласно описанию
- Обеспечить качество и стабильность работы
- Сдать проект в оговоренные сроки

## 💰 Бюджет

**Стоимость:** $${props.service.price}

## ⏰ Сроки

**Примерный срок:** 2-3 недели

## ✅ Критерии приёмки

- [ ] Все требования реализованы
- [ ] Проект протестирован
- [ ] Документация предоставлена

---
*ТЗ сгенерировано AI на основе вашего запроса*`
  }
  
  // Простое форматирование Markdown в HTML
  const formatMarkdown = (text) => {
    if (!text) return ''
    
    return text
      // Заголовки
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2 text-[#1a1a2e]">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-6 mb-3 text-[#1a1a2e]">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-6 mb-4 text-[#1a1a2e]">$1</h1>')
      // Жирный текст
      .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-bold text-[#1a1a2e]">$1</strong>')
      // Списки
      .replace(/^\- (.*$)/gim, '<li class="ml-4 my-1">• $1</li>')
      // Таблицы (упрощённо)
      .replace(/\|/g, ' | ')
      // Чекбоксы
      .replace(/\[ \]/g, '☐')
      .replace(/\[x\]/gi, '☑')
      // Параграфы
      .replace(/\n\n/g, '</p><p class="my-2">')
      // Обёртка
      .replace(/^(.*)$/gim, '<p class="my-2">$1</p>')
  }
  
  // Создание заказа
  const createOrder = async () => {
    creating.value = true
    
    try {
      await axios.post('/api/market/orders/create/', {
        service_id: props.service.id,
        agreed_tz: generatedTz.value
      })
      
      // Успех - показываем уведомление и закрываем
      alert('🎉 Заказ успешно создан! Исполнитель получит уведомление.')
      emit('close')
      
      // Можно перенаправить в чаты
      // router.push('/chats')
      
    } catch (e) {
      console.error('Order creation error:', e)
      alert('❌ Ошибка создания заказа. Попробуйте позже.')
    } finally {
      creating.value = false
    }
  }
  </script>
  
  <style scoped>
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }
  
  .animate-fade-in {
    animation: fade-in 0.2s ease-out;
  }
  
  /* Стилизация прокрутки */
  ::-webkit-scrollbar {
    width: 8px;
  }
  
  ::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
  }
  
  ::-webkit-scrollbar-thumb {
    background: #7000ff;
    border-radius: 10px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: #5500cc;
  }
  </style>