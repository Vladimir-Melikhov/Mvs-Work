<!-- frontend/src/components/MedusaCardSetup.vue -->
<!--
  Компонент управления картой для безопасных сделок (Medusa).
  Показывается в профиле воркера.

  Исправленный флоу:
    1. Регистрация получателя в Точке (один раз)
    2. Получение ссылки на форму → открытие в новой вкладке
    3. Пользователь вводит карту на сайте Точки
    4. Возвращается → нажимает «Обновить» → сервер проверяет через Tochka API
    5. Карта подтверждена → показываем как привязанную
-->
<template>
  <div class="glass rounded-[24px] md:rounded-[32px] p-4 md:p-6 border border-white/20">

    <!-- Заголовок -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-[#7000ff]/10 flex items-center justify-center">
          <svg class="w-5 h-5 text-[#7000ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        </div>
        <div>
          <h3 class="text-sm md:text-base font-bold text-[#1a1a2e]">Безопасные сделки</h3>
          <p class="text-[10px] md:text-xs text-gray-500">Карта для получения выплат</p>
        </div>
      </div>

      <!-- Статус -->
      <div
        class="flex items-center gap-1.5 px-2 md:px-3 py-1 rounded-full text-[9px] md:text-[10px] font-bold uppercase tracking-widest"
        :class="hasCard
          ? 'bg-green-50 text-green-600 border border-green-200'
          : isRegistered
            ? 'bg-blue-50 text-blue-600 border border-blue-200'
            : 'bg-amber-50 text-amber-600 border border-amber-200'"
      >
        <span
          class="w-1.5 h-1.5 rounded-full"
          :class="hasCard ? 'bg-green-500' : isRegistered ? 'bg-blue-500' : 'bg-amber-500'"
        ></span>
        {{ hasCard ? 'Подключено' : isRegistered ? 'Ожидает карту' : 'Не настроено' }}
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <div class="w-6 h-6 border-2 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
    </div>

    <!-- Карта привязана -->
    <div v-else-if="hasCard" class="space-y-3">
      <div class="bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] rounded-2xl p-4 text-white relative overflow-hidden">
        <div class="absolute top-0 right-0 w-32 h-32 bg-[#7000ff] rounded-full blur-[60px] opacity-20 translate-x-1/3 -translate-y-1/3"></div>
        <div class="relative">
          <div class="text-[10px] uppercase tracking-wider text-white/50 mb-3">Карта для выплат</div>
          <div class="text-lg font-mono tracking-widest mb-4">
            •••• •••• •••• {{ cardMaskedPan }}
          </div>
          <div class="flex items-center justify-between">
            <div class="text-xs text-white/60">Привязана к MVS-Work</div>
            <svg class="w-8 h-5 text-white/40" viewBox="0 0 48 30" fill="currentColor">
              <circle cx="15" cy="15" r="15" opacity="0.8"/>
              <circle cx="33" cy="15" r="15" opacity="0.6"/>
            </svg>
          </div>
        </div>
      </div>

      <div class="flex gap-2">
        <button
          @click="refreshInfo"
          :disabled="refreshing"
          class="flex-1 py-2 rounded-xl text-xs font-bold text-gray-600 bg-white/20 hover:bg-white/40 transition-all border border-white/30"
        >
          {{ refreshing ? 'Обновление...' : 'Обновить' }}
        </button>
        <button
          @click="showDeleteConfirm = true"
          class="px-4 py-2 rounded-xl text-xs font-bold text-red-500 bg-red-50/50 hover:bg-red-50 transition-all border border-red-200/50"
        >
          Удалить
        </button>
      </div>
    </div>

    <!-- Карта НЕ привязана -->
    <div v-else class="space-y-3">

      <!-- Шаг 1: Регистрация -->
      <div v-if="!isRegistered" class="space-y-3">
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm text-amber-800">
          <div class="font-bold mb-1 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Шаг 1 из 2: Регистрация
          </div>
          <div class="text-xs">Зарегистрируйтесь как получатель выплат в Точка Банке. Это нужно сделать один раз.</div>
        </div>

        <button
          @click="registerRecipient"
          :disabled="registering"
          class="w-full py-3 rounded-xl font-bold text-sm text-white bg-[#7000ff] hover:bg-[#5500cc] transition-all shadow-lg shadow-[#7000ff]/20 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span v-if="registering" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <span v-else class="flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Зарегистрироваться как получатель
          </span>
        </button>
      </div>

      <!-- Шаг 2: Привязка карты -->
      <div v-else class="space-y-3">

        <!-- Ожидание подтверждения карты (форма открыта) -->
        <div v-if="waitingForCard" class="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div class="font-bold text-blue-800 mb-2 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Форма открыта в новой вкладке
          </div>
          <div class="text-xs text-blue-700 mb-3">
            Введите данные карты на сайте Точка Банка и вернитесь сюда.
            После заполнения нажмите «Я привязал карту».
          </div>
          <div class="flex gap-2">
            <button
              @click="openCardForm"
              class="flex-1 py-2 rounded-xl text-xs font-bold text-blue-600 border border-blue-300 hover:bg-blue-50 transition-all"
            >
              Открыть форму снова
            </button>
            <button
              @click="confirmCard"
              :disabled="confirming"
              class="flex-1 py-2 rounded-xl text-xs font-bold text-white bg-[#1a1a2e] hover:bg-black transition-all disabled:opacity-50"
            >
              {{ confirming ? 'Проверяем...' : 'Я привязал карту' }}
            </button>
          </div>
        </div>

        <!-- Начальное состояние: зарегистрированы, но без карты -->
        <template v-else>
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-3 text-sm text-blue-800">
            <div class="font-bold mb-1">Шаг 2 из 2: Привязка карты</div>
            <div class="text-xs">Нажмите кнопку ниже — откроется безопасная форма Точка Банка для ввода данных карты.</div>
          </div>

          <button
            @click="addCard"
            :disabled="addingCard"
            class="w-full py-3 rounded-xl font-bold text-sm text-white bg-[#1a1a2e] hover:bg-black transition-all shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span v-if="addingCard" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span v-else class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              Привязать карту
            </span>
          </button>
        </template>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-if="error" class="mt-3 bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-600 font-bold">
      {{ error }}
    </div>

    <!-- Успех -->
    <div v-if="successMessage" class="mt-3 bg-green-50 border border-green-200 rounded-xl p-3 text-xs text-green-700 font-bold">
      {{ successMessage }}
    </div>

    <!-- Модалка подтверждения удаления -->
    <teleport to="body">
      <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl text-center">
          <h3 class="text-lg font-bold mb-2 text-[#1a1a2e]">Удалить карту?</h3>
          <p class="text-sm text-gray-600 mb-4">Вы не сможете получать выплаты по безопасным сделкам, пока не привяжете новую карту.</p>
          <div class="flex gap-3">
            <button @click="showDeleteConfirm = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="deleteCard" :disabled="deleting" class="flex-1 bg-red-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">
              {{ deleting ? 'Удаление...' : 'Удалить' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')
const successMessage = ref('')
const registering = ref(false)
const addingCard = ref(false)
const confirming = ref(false)
const refreshing = ref(false)
const deleting = ref(false)
const showDeleteConfirm = ref(false)
const waitingForCard = ref(false)
const cardFormUrl = ref('')

const isRegistered = computed(() => {
  return auth.user?.profile?.medusa_recipient_registered || false
})

const hasCard = computed(() => {
  return auth.user?.profile?.medusa_card_linked || false
})

const cardMaskedPan = computed(() => {
  const pan = auth.user?.profile?.medusa_card_masked_pan || ''
  return pan.replace(/[^\d*]/g, '').slice(-4) || '••••'
})

const clearMessages = () => {
  error.value = ''
  successMessage.value = ''
}

/**
 * Загрузка актуальных данных с сервера (с синхронизацией через Tochka API).
 */
const fetchRecipientInfo = async () => {
  loading.value = true
  clearMessages()
  try {
    const res = await axios.get('/api/market/medusa/recipient-info/')
    if (res.data.status === 'success') {
      // Сервер синхронизировался с Tochka — обновляем локальный профиль
      await auth.fetchProfile()

      // Если карта подтверждена — сбрасываем состояние ожидания
      if (res.data.data.has_card) {
        waitingForCard.value = false
        cardFormUrl.value = ''
        successMessage.value = 'Карта успешно привязана!'
        setTimeout(() => { successMessage.value = '' }, 4000)
      }
    }
  } catch (e) {
    if (e.response?.status !== 502) {
      console.error('[Medusa] Ошибка получения данных:', e)
    }
  } finally {
    loading.value = false
  }
}

/**
 * Регистрация воркера как получателя в Tochka.
 */
const registerRecipient = async () => {
  registering.value = true
  clearMessages()
  try {
    const res = await axios.post('/api/market/medusa/register-recipient/')
    if (res.data.status === 'success') {
      await auth.fetchProfile()
      successMessage.value = 'Зарегистрированы! Теперь привяжите карту.'
    } else {
      error.value = res.data.error || 'Ошибка регистрации'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка связи с банком'
  } finally {
    registering.value = false
  }
}

/**
 * Получить ссылку на форму привязки карты и открыть её в новой вкладке.
 */
const addCard = async () => {
  addingCard.value = true
  clearMessages()
  try {
    const res = await axios.post('/api/market/medusa/add-card/')
    if (res.data.status === 'success') {
      const formUrl = res.data.data.form_url
      cardFormUrl.value = formUrl
      window.open(formUrl, '_blank')
      waitingForCard.value = true
    } else {
      if (res.data.action_required === 'register_recipient') {
        error.value = 'Сначала зарегистрируйтесь как получатель'
        await auth.fetchProfile()
      } else {
        error.value = res.data.error || 'Ошибка получения формы'
      }
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка связи с банком'
  } finally {
    addingCard.value = false
  }
}

/**
 * Открыть форму ещё раз (если пользователь закрыл вкладку).
 */
const openCardForm = () => {
  if (cardFormUrl.value) {
    window.open(cardFormUrl.value, '_blank')
  }
}

/**
 * Проверить через сервер, была ли карта успешно привязана (синхронизация с Tochka).
 */
const confirmCard = async () => {
  confirming.value = true
  clearMessages()
  try {
    const res = await axios.get('/api/market/medusa/recipient-info/')
    if (res.data.status === 'success') {
      await auth.fetchProfile()
      if (res.data.data.has_card) {
        waitingForCard.value = false
        cardFormUrl.value = ''
        successMessage.value = 'Карта успешно привязана!'
        setTimeout(() => { successMessage.value = '' }, 4000)
      } else {
        error.value = 'Карта ещё не привязана. Убедитесь, что прошли форму до конца, и попробуйте снова.'
      }
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка проверки. Попробуйте позже.'
  } finally {
    confirming.value = false
  }
}

/**
 * Обновить информацию (кнопка «Обновить» при наличии карты).
 */
const refreshInfo = async () => {
  refreshing.value = true
  clearMessages()
  try {
    await fetchRecipientInfo()
  } finally {
    refreshing.value = false
  }
}

/**
 * Удалить карту.
 */
const deleteCard = async () => {
  const cardId = auth.user?.profile?.medusa_card_ext_id
  if (!cardId) return

  deleting.value = true
  clearMessages()
  try {
    const res = await axios.post('/api/market/medusa/delete-card/', {
      payout_method_ext_id: cardId
    })
    if (res.data.status === 'success') {
      showDeleteConfirm.value = false
      waitingForCard.value = false
      cardFormUrl.value = ''
      await auth.fetchProfile()
      successMessage.value = 'Карта удалена'
      setTimeout(() => { successMessage.value = '' }, 3000)
    } else {
      error.value = res.data.error || 'Ошибка удаления'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка'
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  if (auth.user?.role === 'worker') {
    fetchRecipientInfo()
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07);
}
</style>
