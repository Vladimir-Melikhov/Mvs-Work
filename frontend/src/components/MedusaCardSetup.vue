<!-- frontend/src/components/MedusaCardSetup.vue -->
<!--
  Компонент управления картой для безопасных сделок.

  Флоу:
    1. Не зарегистрирован → кнопка «Зарегистрироваться»
    2. Зарегистрирован, карты нет → кнопка «Привязать карту»
       → форма Tochka в новой вкладке
       → «Я привязал карту» → проверяем через API
    3. Карта привязана → показываем, можно удалить
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

      <div
        class="flex items-center gap-1.5 px-2 md:px-3 py-1 rounded-full text-[9px] md:text-[10px] font-bold uppercase tracking-widest"
        :class="statusBadgeClass"
      >
        <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass"></span>
        {{ statusLabel }}
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="initialLoading" class="flex items-center justify-center py-8">
      <div class="w-6 h-6 border-2 border-[#7000ff]/30 border-t-[#7000ff] rounded-full animate-spin"></div>
    </div>

    <!-- Карта привязана -->
    <div v-else-if="hasCard" class="space-y-3">
      <div class="bg-gradient-to-br from-[#1a1a2e] to-[#2a2a4e] rounded-2xl p-4 text-white relative overflow-hidden">
        <div class="absolute top-0 right-0 w-32 h-32 bg-[#7000ff] rounded-full blur-[60px] opacity-20 translate-x-1/3 -translate-y-1/3"></div>
        <div class="relative">
          <div class="text-[10px] uppercase tracking-wider text-white/50 mb-3">Карта для выплат</div>
          <div class="text-lg font-mono tracking-widest mb-4">
            {{ displayMaskedPan }}
          </div>
          <div class="flex items-center justify-between">
            <div class="text-xs text-white/60">Мвс-Работа</div>
          </div>
        </div>
      </div>

      <button
        @click="showDeleteConfirm = true"
        class="w-full py-2 rounded-xl text-xs font-bold text-[#7000ff] bg-[#7000ff]/10 hover:bg-[#7000ff]/20 transition-all border border-[#7000ff]/30"
      >
        Удалить карту
      </button>
    </div>

    <!-- Карта НЕ привязана -->
    <div v-else class="space-y-3">

      <!-- Шаг 1: нужна регистрация -->
      <div v-if="!isRegistered" class="space-y-3">
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm text-amber-800">
          <div class="font-bold mb-1 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Шаг 1 из 2: Регистрация
          </div>
          <div class="text-xs">Зарегистрируйтесь как получатель выплат в Точка Банке.</div>
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
            Зарегистрироваться
          </span>
        </button>
      </div>

      <!-- Шаг 2: привязка карты -->
      <div v-else class="space-y-3">

        <!-- Форма открыта, ждём подтверждения -->
        <div v-if="formOpened" class="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div class="font-bold text-blue-800 mb-2 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Форма открыта в новой вкладке
          </div>
          <div class="text-xs text-blue-700 mb-3">
            Введите данные карты на сайте Точка Банка и вернитесь сюда.
            После завершения нажмите «Я привязал карту».
          </div>
          <div class="flex gap-2">
            <button
              @click="openCardForm"
              class="flex-1 py-2 rounded-xl text-xs font-bold text-blue-600 border border-blue-300 hover:bg-blue-50 transition-all"
            >
              Открыть снова
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

        <!-- Начальное: готов привязать -->
        <template v-else>
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-3 text-sm text-blue-800">
            <div class="font-bold mb-1">Шаг 2 из 2: Привязка карты</div>
            <div class="text-xs">Нажмите кнопку ниже — откроется форма Точка Банка для ввода карты.</div>
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
          <p class="text-sm text-gray-600 mb-4">
            Вы не сможете получать выплаты по безопасным сделкам, пока не привяжете новую карту.
          </p>
          <div class="flex gap-3">
            <button
              @click="showDeleteConfirm = false"
              class="flex-1 border-2 py-2 rounded-lg text-sm font-bold"
            >
              Отмена
            </button>
            <button
              @click="deleteCard"
              :disabled="deleting"
              class="flex-1 bg-red-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm"
            >
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

// Состояния
const initialLoading = ref(true)
const registering = ref(false)
const addingCard = ref(false)
const confirming = ref(false)
const deleting = ref(false)
const showDeleteConfirm = ref(false)

// Форма открыта
const formOpened = ref(false)
const cardFormUrl = ref('')

// Сообщения
const error = ref('')
const successMessage = ref('')

// Данные из API
const recipientInfo = ref({
  registered: false,
  has_card: false,
  cards: [],
  recipient_ext_id: null,
  card_ext_id: null,
  medusa_card_ext_id: null,
})

// Computed
const isRegistered = computed(() => recipientInfo.value.registered)
const hasCard = computed(() => recipientInfo.value.has_card)

const displayMaskedPan = computed(() => {
  if (!recipientInfo.value.cards.length) return '•••• •••• •••• ••••'
  const pan = recipientInfo.value.cards[0]?.masked_pan || '****'
  const digits = pan.replace(/[^0-9]/g, '').slice(-4)
  return `•••• •••• •••• ${digits.padStart(4, '•')}`
})

const statusLabel = computed(() => {
  if (hasCard.value) return 'Подключено'
  if (isRegistered.value) return 'Ожидает карту'
  return 'Не настроено'
})

const statusBadgeClass = computed(() => {
  if (hasCard.value) return 'bg-green-50 text-green-600 border border-green-200'
  if (isRegistered.value) return 'bg-blue-50 text-blue-600 border border-blue-200'
  return 'bg-amber-50 text-amber-600 border border-amber-200'
})

const statusDotClass = computed(() => {
  if (hasCard.value) return 'bg-green-500'
  if (isRegistered.value) return 'bg-blue-500'
  return 'bg-amber-500'
})

const clearMessages = () => {
  error.value = ''
  successMessage.value = ''
}

// ─── Загрузка данных ─────────────────────────────────────────────────────────

const loadRecipientInfo = async () => {
  clearMessages()
  try {
    const res = await axios.get('/api/market/medusa/recipient-info/')
    if (res.data.status === 'success') {
      recipientInfo.value = res.data.data

      if (recipientInfo.value.has_card) {
        formOpened.value = false
        cardFormUrl.value = ''
      }
    }
  } catch (e) {
    console.error('[Medusa] recipient-info ошибка:', e)
  }
}

// ─── Регистрация получателя ──────────────────────────────────────────────────

const registerRecipient = async () => {
  registering.value = true
  clearMessages()
  try {
    const res = await axios.post('/api/market/medusa/register-recipient/')
    if (res.data.status === 'success') {
      successMessage.value = 'Регистрация успешна! Теперь привяжите карту.'
      await loadRecipientInfo()
      setTimeout(() => { successMessage.value = '' }, 4000)
    } else {
      error.value = res.data.error || 'Ошибка регистрации'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка связи с сервером'
  } finally {
    registering.value = false
  }
}

// ─── Привязка карты ──────────────────────────────────────────────────────────

const addCard = async () => {
  addingCard.value = true
  clearMessages()
  try {
    const res = await axios.post('/api/market/medusa/add-card/')
    if (res.data.status === 'success') {
      const formUrl = res.data.data.form_url
      cardFormUrl.value = formUrl
      window.open(formUrl, '_blank')
      formOpened.value = true
    } else {
      if (res.data.action_required === 'register_recipient') {
        error.value = 'Сначала зарегистрируйтесь как получатель'
        await loadRecipientInfo()
      } else {
        error.value = res.data.error || 'Ошибка получения формы'
      }
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка связи с сервером'
  } finally {
    addingCard.value = false
  }
}

const openCardForm = () => {
  if (cardFormUrl.value) {
    window.open(cardFormUrl.value, '_blank')
  }
}

const confirmCard = async () => {
  confirming.value = true
  clearMessages()
  try {
    await loadRecipientInfo()

    if (recipientInfo.value.has_card) {
      successMessage.value = 'Карта успешно привязана!'
      setTimeout(() => { successMessage.value = '' }, 4000)
    } else {
      error.value = 'Карта ещё не привязана. Убедитесь, что прошли форму до конца, и попробуйте снова через несколько секунд.'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка проверки'
  } finally {
    confirming.value = false
  }
}

// ─── Удаление карты ──────────────────────────────────────────────────────────

const deleteCard = async () => {
  // Ищем ext_id карты из всех доступных источников
  const cardExtId =
    recipientInfo.value.cards?.[0]?.ext_id ||
    recipientInfo.value.card_ext_id ||
    recipientInfo.value.medusa_card_ext_id

  if (!cardExtId) {
    error.value = 'Не найден id карты для удаления.'
    showDeleteConfirm.value = false
    return
  }

  deleting.value = true
  clearMessages()
  try {
    const res = await axios.post('/api/market/medusa/delete-card/', {
      payout_method_ext_id: cardExtId,
    })
    if (res.data.status === 'success') {
      showDeleteConfirm.value = false
      formOpened.value = false
      cardFormUrl.value = ''
      successMessage.value = 'Карта удалена'
      await loadRecipientInfo()
      setTimeout(() => { successMessage.value = '' }, 3000)
    } else {
      error.value = res.data.error || 'Ошибка удаления'
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Ошибка связи с сервером'
  } finally {
    deleting.value = false
  }
}

// ─── Инициализация ───────────────────────────────────────────────────────────

onMounted(async () => {
  if (auth.user?.role !== 'worker') {
    initialLoading.value = false
    return
  }

  try {
    await loadRecipientInfo()
  } finally {
    initialLoading.value = false
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