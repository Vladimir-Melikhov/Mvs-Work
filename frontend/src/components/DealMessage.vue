<!-- frontend/src/components/DealMessage.vue -->
<!--
  ОБНОВЛЁННЫЙ DealMessage.vue — интеграция с Безопасными сделками Точка Банка.
  
  Изменения:
    1. Кнопка «Оплатить» для эскроу → вызывает /api/market/medusa/create-payment/
       и открывает ссылку на оплату банка
    2. Кнопка «Принять работу» для эскроу → вызывает /api/market/medusa/confirm-deal/
    3. Отказ/спор для эскроу → вызывает /api/market/medusa/reject-deal/
    4. Отображение комиссий и суммы к оплате
    5. Проверка статуса оплаты
    6. Предупреждение если у воркера не привязана карта
    
  Всё остальное (неэскроу, доработки, споры) — без изменений.
-->
<template>
  <div 
    :class="sidebarMode ? '' : 'deal-card-wrapper w-full flex justify-center my-6 px-4'"
  >
    <div 
      class="deal-card glass rounded-[32px] p-6 border-2 shadow-2xl"
      :class="[
        borderColor, 
        sidebarMode 
          ? 'w-full max-h-[500px] flex flex-col' 
          : 'max-w-md w-full'
      ]"
    >
      
      <!-- Заголовок -->
      <div class="flex items-center gap-3 mb-4 shrink-0">
        <div class="w-14 h-14 rounded-full flex items-center justify-center text-white shadow-lg shrink-0" :class="statusIconBg">
          <svg v-if="dealData.status === 'pending'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else-if="dealData.status === 'accepted'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <svg v-else-if="dealData.status === 'paid'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <svg v-else-if="dealData.status === 'delivered'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <svg v-else-if="dealData.status === 'dispute'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <svg v-else-if="dealData.status === 'completed'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else-if="dealData.status === 'cancelled'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <svg v-else class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-[10px] font-bold uppercase tracking-widest" :class="statusTextColor">
            {{ statusLabel }}
          </div>
          <div class="text-lg font-bold text-[#1a1a2e] truncate">{{ dealData.title }}</div>
          <div v-if="dealData.is_escrow" class="flex items-center gap-1 mt-0.5">
            <span class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#7000ff]/10 text-[#7000ff]">
              Безопасная сделка
            </span>
          </div>
        </div>
      </div>

      <div 
        :class="sidebarMode 
          ? 'flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin min-h-0' 
          : 'space-y-4'"
      >

        <!-- Финансы -->
        <div class="bg-gradient-to-br from-purple-50 to-violet-50 rounded-2xl p-4 border border-purple-200 shrink-0">
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600">Стоимость работы:</span>
              <span class="font-bold">{{ parseInt(dealData.price) }}₽</span>
            </div>
            <!-- Комиссии Medusa (показываем только для эскроу) -->
            <template v-if="dealData.is_escrow && commissionInfo">
              <div class="border-t border-purple-200/50 pt-1 mt-1"></div>
              <div class="flex justify-between text-xs text-gray-500">
                <span>Комиссия сервиса ({{ commissionRateDisplay }}):</span>
                <span>{{ commissionInfo.total }}₽</span>
              </div>
              <div class="flex justify-between font-bold text-[#7000ff]">
                <span>Итого к оплате:</span>
                <span>{{ commissionInfo.totalAmount }}₽</span>
              </div>
            </template>
          </div>
        </div>

        <!-- ПЕРЕКЛЮЧАТЕЛЬ ТИПА СДЕЛКИ (только для клиента в статусе pending) -->
        <div 
          v-if="showEscrowToggle"
          class="shrink-0"
        >
          <div class="rounded-xl border-2 p-4 transition-all"
            :class="localIsEscrow
              ? 'bg-[#7000ff]/5 border-[#7000ff]/30'
              : 'bg-gray-50 border-gray-200'"
          >
            <label class="flex items-start gap-3 cursor-pointer">
              <input 
                type="checkbox" 
                v-model="localIsEscrow"
                class="mt-0.5 w-5 h-5 text-[#7000ff] rounded border-gray-300 focus:ring-2 focus:ring-[#7000ff]/20 shrink-0"
              >
              <div class="flex-1 min-w-0">
                <div class="font-bold text-[#1a1a2e] mb-1 flex items-center gap-2 flex-wrap">
                  <svg class="w-4 h-4" :class="localIsEscrow ? 'text-[#7000ff]' : 'text-gray-400'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>Безопасная сделка</span>
                </div>
                <div class="text-xs text-gray-600 break-words">
                  {{ localIsEscrow 
                    ? 'Средства хранятся в банке до завершения работы — максимальная защита' 
                    : 'Оплата по договорённости, упрощённый процесс без споров и доработок' }}
                </div>
              </div>
            </label>
          </div>
        </div>

        <!-- Результат спора -->
        <div v-if="dealData.dispute_result" class="shrink-0">
          <div 
            :class="[
              'rounded-xl p-4 border-2',
              dealData.dispute_result.winner === 'client' ? 'bg-purple-50 border-purple-300' : 'bg-indigo-50 border-indigo-300'
            ]"
          >
            <div class="text-sm font-bold mb-2 flex items-center gap-2"
                 :class="dealData.dispute_result.winner === 'client' ? 'text-purple-800' : 'text-indigo-800'">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ dealData.dispute_result.message }}
            </div>
            <div class="text-xs" :class="dealData.dispute_result.winner === 'client' ? 'text-purple-600' : 'text-indigo-600'">
              {{ dealData.dispute_result.winner === 'client' ? 'Средства возвращены клиенту' : 'Средства выплачены исполнителю' }}
            </div>
          </div>
        </div>

        <!-- Информация о споре -->
        <div v-if="dealData.status === 'dispute'" class="shrink-0">
          <div class="bg-fuchsia-50 border border-fuchsia-200 rounded-xl p-4 mb-3">
            <div class="text-xs font-bold text-fuchsia-800 uppercase tracking-wider mb-2 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Претензия клиента
            </div>
            <div class="text-sm text-fuchsia-900 whitespace-pre-line leading-relaxed">{{ dealData.dispute_client_reason }}</div>
          </div>

          <div v-if="dealData.dispute_worker_defense" class="bg-violet-50 border border-violet-200 rounded-xl p-4 mb-3">
            <div class="text-xs font-bold text-violet-800 uppercase tracking-wider mb-2 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Защита исполнителя
            </div>
            <div class="text-sm text-violet-900 whitespace-pre-line leading-relaxed">{{ dealData.dispute_worker_defense }}</div>
          </div>

          <div v-if="dealData.is_dispute_pending_admin" class="bg-purple-50 border border-purple-200 rounded-xl p-3 text-sm text-purple-800">
            <div class="font-bold mb-1 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Ожидает решения администратора
            </div>
            <div>Обе стороны представили свои аргументы. Решение принимает администратор.</div>
          </div>
        </div>

        <!-- Доработки (только для эскроу) -->
        <div v-if="dealData.is_escrow && dealData.revision_count > 0" class="shrink-0">
          <div class="bg-purple-50 border border-purple-200 rounded-xl p-3 text-sm">
            <span class="font-bold text-purple-800">Доработки: {{ dealData.revision_count }}/{{ dealData.max_revisions }}</span>
          </div>
        </div>

        <!-- Результат работы (delivered) -->
        <div v-if="dealData.status === 'delivered' && dealData.delivery_message" class="shrink-0">
          <div class="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
            <div class="text-xs font-bold text-indigo-800 uppercase tracking-wider mb-2">Результат работы</div>
            <div class="text-sm text-indigo-900 whitespace-pre-line leading-relaxed">{{ dealData.delivery_message }}</div>
          </div>
        </div>
        
        <!-- Вложения -->
        <div v-if="dealData.delivery_attachments && dealData.delivery_attachments.length > 0" class="shrink-0">
          <div class="bg-violet-50 border border-violet-200 rounded-xl p-4">
            <div class="text-xs font-bold text-violet-800 uppercase tracking-wider mb-2">Прикрепленные файлы</div>
            <div class="space-y-2">
              <a 
                v-for="att in dealData.delivery_attachments" 
                :key="att.id"
                :href="att.url" 
                :download="att.filename"
                class="flex items-center gap-2 p-2 rounded-lg bg-white hover:bg-violet-100 transition-all text-sm group"
              >
                <svg class="w-4 h-4 text-violet-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                <span class="truncate text-violet-900 flex-1">{{ att.filename }}</span>
                <svg class="w-4 h-4 text-violet-600 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </a>
            </div>
          </div>
        </div>
        
        <!-- Завершён -->
        <div v-if="dealData.status === 'completed' && dealData.delivery_message" class="shrink-0">
          <div class="bg-purple-50 border border-purple-200 rounded-xl p-4">
            <div class="text-xs font-bold text-purple-800 uppercase tracking-wider mb-2">Работа завершена</div>
            <div class="text-sm text-purple-900 whitespace-pre-line leading-relaxed">{{ dealData.delivery_message }}</div>
          </div>
        </div>

        <!-- ──────────────── КНОПКИ ДЕЙСТВИЙ ──────────────────────────────── -->
        <div class="space-y-2 pb-2" :class="sidebarMode ? '' : 'mt-auto'">

          <!-- Изменить цену (воркер, pending) -->
          <button 
            v-if="showUpdatePriceButton"
            @click="showPriceModal = true"
            class="w-full border-2 border-purple-300 text-purple-600 py-2 rounded-xl font-bold hover:bg-purple-50 transition-all"
          >
            Изменить цену
          </button>

          <!-- ══════════════════════════════════════════════════════════════════
               ЭСКРОУ: Оплатить через Medusa (реальный платёж)
               ══════════════════════════════════════════════════════════════════ -->
          <button 
            v-if="showPayButton"
            @click="payDealMedusa"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Обработка...
            </span>
            <span v-else class="flex flex-col items-center gap-1">
              <span class="text-base font-bold flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Оплатить безопасно
              </span>
              <span class="text-xs font-normal opacity-90">
                {{ commissionInfo ? commissionInfo.totalAmount + '₽ (вкл. комиссию ' + commissionInfo.total + '₽)' : parseInt(dealData.price) + '₽ + комиссия' }}
              </span>
            </span>
          </button>

          <!-- Кнопка проверки оплаты (если ссылка уже была создана) -->
          <button 
            v-if="showCheckPaymentButton"
            @click="checkPaymentStatus"
            :disabled="loading"
            class="w-full border-2 border-purple-300 text-purple-600 py-2 rounded-xl font-bold hover:bg-purple-50 transition-all flex items-center justify-center gap-2"
          >
            <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <span>Проверить оплату</span>
          </button>

          <!-- КЛИЕНТ: Начать сделку — pending + галочка снята (неэскроу) -->
          <button 
            v-if="showClientStartButton"
            @click="clientStart"
            :disabled="loading"
            class="w-full bg-[#12002b] hover:bg-[#0a001a] text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Обработка...
            </span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Начать сделку
            </span>
          </button>

          <!-- ВОРКЕР: Принять заказ (неэскроу) -->
          <button 
            v-if="showWorkerAcceptButton"
            @click="workerAccept"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Обработка...
            </span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Принять заказ
            </span>
          </button>

          <!-- НЕЭСКРОУ: уведомление для клиента (статус accepted) -->
          <div 
            v-if="showClientAcceptedInfo"
            class="bg-violet-50 border border-violet-200 rounded-xl p-4"
          >
            <div class="flex items-start gap-3">
              <svg class="w-5 h-5 text-violet-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <div class="text-sm text-violet-800">
                <div class="font-bold mb-1">Исполнитель приступил к работе</div>
                <div>Ожидайте результата.</div>
              </div>
            </div>
          </div>

          <!-- Сдать работу (воркер) -->
          <div v-if="showDeliverButton" class="space-y-1">
            <div 
              v-if="!dealData.is_escrow"
              class="text-center text-xs text-amber-600 font-medium px-2"
            >
              Мы не рекомендуем сдавать работу до получения оплаты
            </div>
            <button 
              @click="showDeliveryModal = true"
              class="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
            >
              Сдать работу
            </button>
          </div>

          <!-- ══════════════════════════════════════════════════════════════════
               Принять работу: эскроу → Medusa confirm, неэскроу → обычный complete
               ══════════════════════════════════════════════════════════════════ -->
          <button 
            v-if="showCompleteButton"
            @click="showCompletionModal = true"
            class="w-full bg-gradient-to-r from-violet-500 to-fuchsia-600 hover:from-violet-600 hover:to-fuchsia-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
          >
            {{ dealData.is_escrow ? 'Принять работу и оплатить' : 'Принять и оставить отзыв' }}
          </button>

          <!-- Запросить доработку (только эскроу) -->
          <button 
            v-if="showRevisionButton"
            @click="showRevisionModal = true"
            class="w-full border-2 border-purple-300 text-purple-700 py-2 rounded-xl font-bold hover:bg-purple-50 transition-all"
          >
            Запросить доработку ({{ dealData.revision_count }}/{{ dealData.max_revisions }})
          </button>

          <!-- Открыть спор (только эскроу) -->
          <button 
            v-if="showOpenDisputeButton"
            @click="showDisputeModal = true"
            class="w-full border-2 border-fuchsia-300 text-fuchsia-600 py-2 rounded-xl font-bold hover:bg-fuchsia-50 transition-all flex items-center justify-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Открыть спор
          </button>

          <!-- Вернуть деньги (воркер в споре, только эскроу) -->
          <button 
            v-if="showWorkerRefundButton"
            @click="workerRefund"
            :disabled="loading"
            class="w-full border-2 border-purple-300 text-purple-600 py-2 rounded-xl font-bold hover:bg-purple-50 transition-all disabled:opacity-50"
          >
            <span v-if="loading">Обработка...</span>
            <span v-else>Вернуть деньги</span>
          </button>

          <!-- Оспорить (воркер в споре, только эскроу) -->
          <button 
            v-if="showWorkerDefendButton"
            @click="showDefenseModal = true"
            class="w-full border-2 border-indigo-300 text-indigo-600 py-2 rounded-xl font-bold hover:bg-indigo-50 transition-all"
          >
            Оспорить
          </button>

          <!-- Отменить заказ -->
          <button 
            v-if="showCancelButton"
            @click="showCancelModal = true"
            class="w-full border-2 border-fuchsia-300 text-fuchsia-600 py-2 rounded-xl font-bold hover:bg-fuchsia-50 transition-all"
          >
            Отменить заказ
          </button>
        </div>

      </div>
    </div>

    <!-- МОДАЛЬНЫЕ ОКНА (без изменений — копируем из оригинала) -->
    <teleport to="body">
      <!-- Изменение цены -->
      <div v-if="showPriceModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Изменить цену</h3>
          <p class="text-sm text-gray-600 mb-4">Клиент получит уведомление о новой цене.</p>
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2">Новая цена (₽)</label>
            <input v-model="newPrice" type="number" min="1" class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500" placeholder="Введите новую цену...">
          </div>
          <div class="flex gap-3">
            <button @click="showPriceModal = false; newPrice = parseInt(dealData.price)" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="updatePrice" :disabled="loading || !newPrice || newPrice <= 0" class="flex-1 bg-purple-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Изменить</button>
          </div>
        </div>
      </div>

      <!-- Сдача работы -->
      <div v-if="showDeliveryModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Сдать работу</h3>
          <div v-if="!dealData.is_escrow" class="mb-4 bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm text-amber-800">
            <div class="font-bold mb-1">Внимание</div>
            <div>Мы не рекомендуем сдавать работу до получения оплаты.</div>
          </div>
          <textarea v-model="deliveryMessage" rows="4" class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4 text-sm" placeholder="Опишите что сделано, добавьте ссылки на результат..."></textarea>
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2">Прикрепить файлы (необязательно)</label>
            <label class="cursor-pointer">
              <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-indigo-500 transition-all text-center">
                <svg class="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span class="text-sm text-gray-600">Нажмите для выбора файлов</span>
              </div>
              <input type="file" multiple @change="handleDeliveryFileSelect" class="hidden">
            </label>
            <div v-if="deliveryFiles.length > 0" class="mt-3 space-y-2">
              <div v-for="(file, idx) in deliveryFiles" :key="idx" class="flex items-center gap-2 px-3 py-2 bg-indigo-50 rounded-lg">
                <svg class="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span class="flex-1 text-sm truncate">{{ file.name }}</span>
                <button @click="removeDeliveryFile(idx)" class="text-fuchsia-500 hover:text-fuchsia-700">&times;</button>
              </div>
            </div>
          </div>
          <div class="flex gap-3">
            <button @click="showDeliveryModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="deliverWork" :disabled="!deliveryMessage.trim() || loading" class="flex-1 bg-indigo-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Сдать</button>
          </div>
        </div>
      </div>

      <!-- Завершение с отзывом -->
      <div v-if="showCompletionModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl text-center">
          <h3 class="text-xl font-bold mb-4">
            {{ dealData.is_escrow ? 'Принять работу?' : 'Принять и оставить отзыв?' }}
          </h3>
          <p class="text-sm text-gray-600 mb-6">
            {{ dealData.is_escrow 
              ? 'После принятия деньги будут переведены исполнителю через Точка Банк.' 
              : 'Подтвердите завершение заказа и оставьте отзыв.' }}
          </p>
          <div class="mb-6">
            <label class="block text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Оценка работы</label>
            <div class="flex gap-3 justify-center">
              <button v-for="star in 5" :key="star" @click="rating = star" class="transition-transform hover:scale-125 focus:outline-none">
                <svg class="w-8 h-8" :class="star <= rating ? 'text-yellow-400' : 'text-gray-200'" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </button>
            </div>
          </div>
          <textarea v-model="completionMessage" rows="3" class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 mb-4 text-sm" placeholder="Ваш отзыв..."></textarea>
          <div class="flex gap-3">
            <button @click="showCompletionModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="completeDeal" :disabled="loading || rating === 0" class="flex-1 bg-violet-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">
              {{ dealData.is_escrow ? 'Принять и оплатить' : 'Завершить' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Доработка -->
      <div v-if="showRevisionModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Запросить доработку</h3>
          <p class="text-sm text-gray-600 mb-4">Осталось бесплатных доработок: {{ dealData.max_revisions - dealData.revision_count }}</p>
          <textarea v-model="revisionReason" rows="4" class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 mb-4 text-sm" placeholder="Опишите что нужно доработать..."></textarea>
          <div class="flex gap-3">
            <button @click="showRevisionModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="requestRevision" :disabled="!revisionReason.trim() || loading" class="flex-1 bg-purple-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Запросить</button>
          </div>
        </div>
      </div>

      <!-- Открыть спор -->
      <div v-if="showDisputeModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-2 text-fuchsia-600">Открыть спор</h3>
          <p class="text-sm text-gray-600 mb-4">Опишите, что не так с выполненной работой.</p>
          <textarea v-model="disputeReason" rows="5" class="w-full p-3 rounded-xl border border-fuchsia-200 resize-none focus:outline-none focus:ring-2 focus:ring-fuchsia-500 mb-4 text-sm" placeholder="Подробно опишите проблему..."></textarea>
          <div class="flex gap-3">
            <button @click="showDisputeModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="openDispute" :disabled="!disputeReason.trim() || loading" class="flex-1 bg-fuchsia-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Открыть спор</button>
          </div>
        </div>
      </div>

      <!-- Защита исполнителя -->
      <div v-if="showDefenseModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-2 text-indigo-600">Оспорить претензию</h3>
          <p class="text-sm text-gray-600 mb-4">Представьте свои аргументы. Спор будет передан администратору.</p>
          <textarea v-model="defenseText" rows="5" class="w-full p-3 rounded-xl border border-indigo-200 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4 text-sm" placeholder="Объясните, почему претензия необоснована..."></textarea>
          <div class="flex gap-3">
            <button @click="showDefenseModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="workerDefend" :disabled="!defenseText.trim() || loading" class="flex-1 bg-indigo-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Отправить</button>
          </div>
        </div>
      </div>

      <!-- Отмена заказа -->
      <div v-if="showCancelModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl text-center">
          <h3 class="text-xl font-bold mb-2 text-fuchsia-600">Отменить заказ?</h3>
          <p class="text-sm text-gray-600 mb-4" v-if="dealData.status === 'paid'">Средства будут возвращены клиенту.</p>
          <textarea v-model="cancelReason" rows="3" class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-fuchsia-500 mb-4 text-sm" placeholder="Причина отмены..."></textarea>
          <div class="flex gap-3">
            <button @click="showCancelModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Назад</button>
            <button @click="cancelDeal" :disabled="loading" class="flex-1 bg-fuchsia-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Отменить</button>
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

const props = defineProps({
  message: Object,
  dealData: Object,
  sidebarMode: Boolean
})

const emit = defineEmits(['deal-action'])

const auth = useAuthStore()
const loading = ref(false)

const localIsEscrow = ref(props.dealData.is_escrow ?? true)

// Данные комиссий (загружаются при эскроу)
const commissionInfo = ref(null)
const commissionRateDisplay = '~3.5%'

const dealId = computed(() => {
  return props.dealData.id || props.dealData.deal_id || props.message?.deal_id || props.message?.id
})

// Модалки
const showDeliveryModal = ref(false)
const showCompletionModal = ref(false)
const showRevisionModal = ref(false)
const showCancelModal = ref(false)
const showPriceModal = ref(false)
const showDisputeModal = ref(false)
const showDefenseModal = ref(false)

// Поля ввода
const deliveryMessage = ref('')
const completionMessage = ref('')
const revisionReason = ref('')
const cancelReason = ref('')
const rating = ref(0)
const newPrice = ref(parseInt(props.dealData.price))
const disputeReason = ref('')
const defenseText = ref('')
const deliveryFiles = ref([])

// Роли
const isClient = computed(() => String(auth.user.id) === String(props.dealData.client_id))
const isWorker = computed(() => String(auth.user.id) === String(props.dealData.worker_id))

const showEscrowToggle = computed(() => isClient.value && props.dealData.status === 'pending')

// ── Стили статуса ────────────────────────────────────────────────────────────
const borderColor = computed(() => {
  const colors = { 'pending': 'border-violet-200', 'accepted': 'border-violet-300', 'paid': 'border-purple-300', 'delivered': 'border-indigo-300', 'dispute': 'border-fuchsia-300', 'completed': 'border-purple-400', 'cancelled': 'border-violet-300' }
  return colors[props.dealData.status] || 'border-gray-200'
})

const statusIconBg = computed(() => {
  const bgs = { 'pending': 'bg-gradient-to-br from-violet-400 to-violet-600', 'accepted': 'bg-gradient-to-br from-violet-500 to-purple-600', 'paid': 'bg-gradient-to-br from-purple-500 to-violet-600', 'delivered': 'bg-gradient-to-br from-indigo-500 to-purple-600', 'dispute': 'bg-gradient-to-br from-fuchsia-500 to-pink-600', 'completed': 'bg-gradient-to-br from-purple-600 to-violet-700', 'cancelled': 'bg-gradient-to-br from-violet-500 to-purple-600' }
  return bgs[props.dealData.status] || 'bg-gray-500'
})

const statusLabel = computed(() => {
  if (props.dealData.dispute_result) {
    const winner = props.dealData.dispute_result.winner_text
    if (props.dealData.status === 'cancelled') return `Отменён (спор - победа ${winner})`
    if (props.dealData.status === 'completed') return `Завершён (спор - победа ${winner})`
  }
  const labels = { 'pending': 'Ожидает', 'accepted': 'В работе', 'paid': 'В работе', 'delivered': 'На проверке', 'dispute': 'В споре', 'completed': 'Завершён', 'cancelled': 'Отменён' }
  return labels[props.dealData.status] || props.dealData.status
})

const statusTextColor = computed(() => {
  const colors = { 'pending': 'text-violet-600', 'accepted': 'text-violet-600', 'paid': 'text-purple-600', 'delivered': 'text-indigo-600', 'dispute': 'text-fuchsia-600', 'completed': 'text-purple-700', 'cancelled': 'text-violet-700' }
  return colors[props.dealData.status] || 'text-gray-600'
})

// ── Видимость кнопок ─────────────────────────────────────────────────────────
const showPayButton = computed(() => isClient.value && props.dealData.status === 'pending' && localIsEscrow.value)
const showCheckPaymentButton = computed(() => {
  return isClient.value && props.dealData.status === 'pending' && localIsEscrow.value && props.dealData.medusa_payment_url
})
const showClientStartButton = computed(() => isClient.value && props.dealData.status === 'pending' && !localIsEscrow.value)
const showWorkerAcceptButton = computed(() => isWorker.value && props.dealData.can_worker_accept)
const showClientAcceptedInfo = computed(() => isClient.value && !props.dealData.is_escrow && props.dealData.status === 'accepted')
const showDeliverButton = computed(() => isWorker.value && props.dealData.can_deliver)
const showCompleteButton = computed(() => isClient.value && props.dealData.can_complete)
const showRevisionButton = computed(() => isClient.value && props.dealData.can_request_revision && props.dealData.is_escrow)
const showCancelButton = computed(() => props.dealData.can_cancel)
const showUpdatePriceButton = computed(() => isWorker.value && props.dealData.can_update_price)
const showOpenDisputeButton = computed(() => isClient.value && props.dealData.can_open_dispute && props.dealData.is_escrow)
const showWorkerRefundButton = computed(() => isWorker.value && props.dealData.can_worker_refund && props.dealData.is_escrow)
const showWorkerDefendButton = computed(() => isWorker.value && props.dealData.can_worker_defend && props.dealData.is_escrow)

// ── Загрузка комиссий ────────────────────────────────────────────────────────
const loadCommission = async () => {
  if (!props.dealData.is_escrow || !props.dealData.price) return
  try {
    const res = await axios.get(`/api/market/medusa/calculate-commission/?price=${parseInt(props.dealData.price)}`)
    if (res.data.status === 'success') {
      const d = res.data.data
      commissionInfo.value = {
        platform: d.platform_commission,
        tochka: d.medusa_commission,
        acquiring: d.acquiring_commission,
        total: d.total_commission,
        totalAmount: d.total_amount,
      }
    }
  } catch (e) {
    console.log('[Medusa] Не удалось загрузить комиссии:', e.message)
  }
}

onMounted(() => {
  if (props.dealData.is_escrow && props.dealData.status === 'pending') {
    loadCommission()
  }
  // Если комиссии уже сохранены в deal_data
  if (props.dealData.medusa_total_commission) {
    commissionInfo.value = {
      platform: props.dealData.medusa_platform_commission,
      tochka: props.dealData.medusa_tochka_commission,
      acquiring: props.dealData.medusa_acquiring_commission,
      total: props.dealData.medusa_total_commission,
      totalAmount: props.dealData.medusa_total_amount,
    }
  }
})

// ── Действия ─────────────────────────────────────────────────────────────────

// ═══ ЭСКРОУ: Оплатить через Medusa ═══
const payDealMedusa = async () => {
  loading.value = true
  try {
    const res = await axios.post('/api/market/medusa/create-payment/', {
      deal_id: dealId.value
    })

    if (res.data.status === 'success') {
      const paymentUrl = res.data.data.payment_url
      
      // Обновляем комиссии
      if (res.data.data.commission_details) {
        commissionInfo.value = {
          platform: res.data.data.commission_details.platform,
          tochka: res.data.data.commission_details.tochka,
          acquiring: res.data.data.commission_details.acquiring,
          total: res.data.data.commission_details.total,
          totalAmount: res.data.data.total_amount,
        }
      }

      // Открываем страницу оплаты
      if (paymentUrl) {
        window.open(paymentUrl, '_blank')
      }
      
      emit('deal-action')
    } else {
      const error = res.data.error || 'Ошибка создания платежа'
      if (res.data.action_required === 'worker_card_required') {
        alert('Исполнитель ещё не привязал карту для выплат.\n\nПопросите исполнителя зайти в профиль и привязать банковскую карту в разделе «Безопасные сделки».')
      } else {
        alert(error)
      }
    }
  } catch (e) {
    const errorMsg = e.response?.data?.error || e.message
    if (errorMsg.includes('карт') || errorMsg.includes('card')) {
      alert('Исполнитель ещё не привязал карту для выплат.\n\nПопросите исполнителя настроить карту в профиле.')
    } else {
      alert('Ошибка: ' + errorMsg)
    }
  } finally {
    loading.value = false
  }
}

// Проверка статуса оплаты
const checkPaymentStatus = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/market/medusa/payment-status/${dealId.value}/`)
    if (res.data.status === 'success') {
      const d = res.data.data
      if (d.medusa_status === 'paid') {
        alert('Оплата прошла успешно! Деньги заморожены.')
      } else {
        alert(d.message || `Статус: ${d.medusa_status}`)
      }
      emit('deal-action')
    }
  } catch (e) {
    alert('Ошибка проверки: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

// Неэскроу: клиент запускает сделку
const clientStart = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/client-start/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const updatePrice = async () => {
  loading.value = true
  try {
    await axios.patch(`/api/market/deals/${dealId.value}/update-price/`, { price: newPrice.value })
    showPriceModal.value = false
    emit('deal-action')
    // Пересчитать комиссии
    loadCommission()
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const workerAccept = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/worker-accept/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const deliverWork = async () => {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('delivery_message', deliveryMessage.value)
    deliveryFiles.value.forEach(file => formData.append('files', file))
    await axios.post(`/api/market/deals/${dealId.value}/deliver/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    showDeliveryModal.value = false
    deliveryMessage.value = ''
    deliveryFiles.value = []
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

// ═══ Завершение: эскроу → Medusa confirm + review, неэскроу → обычный complete ═══
const completeDeal = async () => {
  if (rating.value === 0) { alert('Поставьте оценку'); return }
  loading.value = true
  try {
    // Для эскроу: сначала подтверждаем в Medusa (выплата)
    if (props.dealData.is_escrow && props.dealData.medusa_order_ext_id) {
      await axios.post(`/api/market/medusa/confirm-deal/${dealId.value}/`)
    }
    
    // Затем завершаем сделку + отзыв (работает и для эскроу, и для неэскроу)
    await axios.post(`/api/market/deals/${dealId.value}/complete/`, {
      rating: rating.value,
      comment: completionMessage.value || 'Спасибо!'
    })
    
    showCompletionModal.value = false
    completionMessage.value = ''
    rating.value = 0
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const handleDeliveryFileSelect = (event) => {
  const files = Array.from(event.target.files)
  const validFiles = files.filter(file => {
    if (file.size > 20 * 1024 * 1024) { alert(`Файл ${file.name} слишком большой (макс 20MB)`); return false }
    return true
  })
  deliveryFiles.value.push(...validFiles)
  event.target.value = ''
}

const removeDeliveryFile = (index) => deliveryFiles.value.splice(index, 1)

const requestRevision = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/revision/`, { revision_reason: revisionReason.value })
    showRevisionModal.value = false
    revisionReason.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const openDispute = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/open-dispute/`, { dispute_reason: disputeReason.value })
    showDisputeModal.value = false
    disputeReason.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const workerRefund = async () => {
  if (!confirm('Вернуть деньги клиенту? Это действие нельзя отменить.')) return
  loading.value = true
  try {
    // Для эскроу: отклоняем в Medusa (возврат)
    if (props.dealData.is_escrow && props.dealData.medusa_order_ext_id) {
      await axios.post(`/api/market/medusa/reject-deal/${dealId.value}/`)
    }
    await axios.post(`/api/market/deals/${dealId.value}/worker-refund/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const workerDefend = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/worker-defend/`, { defense_text: defenseText.value })
    showDefenseModal.value = false
    defenseText.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const cancelDeal = async () => {
  loading.value = true
  try {
    // Для эскроу с оплатой: отклоняем в Medusa (возврат)
    if (props.dealData.is_escrow && props.dealData.medusa_order_ext_id && props.dealData.status === 'paid') {
      await axios.post(`/api/market/medusa/reject-deal/${dealId.value}/`)
    }
    await axios.post(`/api/market/deals/${dealId.value}/cancel/`, { reason: cancelReason.value || 'Не указана' })
    showCancelModal.value = false
    cancelReason.value = ''
    emit('deal-action')
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
}

.scrollbar-thin::-webkit-scrollbar { width: 6px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(124, 58, 237, 0.3); border-radius: 10px; }
.scrollbar-thin::-webkit-scrollbar-thumb:hover { background: rgba(124, 58, 237, 0.5); }
</style>
