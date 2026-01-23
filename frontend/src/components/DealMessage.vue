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
      
      <div class="flex items-center gap-3 mb-4 shrink-0">
        <div class="w-14 h-14 rounded-full flex items-center justify-center text-white shadow-lg shrink-0" :class="statusIconBg">
          <svg v-if="dealData.status === 'pending'" class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
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
        </div>
      </div>

      <div 
        :class="sidebarMode 
          ? 'flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin min-h-0' 
          : 'space-y-4'"
      >

        <div class="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-4 border border-purple-200 shrink-0">
          <div class="space-y-1 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600">Стоимость работы:</span>
              <span class="font-bold">{{ dealData.price }}₽</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Комиссия сервиса (8%):</span>
              <span class="font-bold">{{ dealData.commission }}₽</span>
            </div>
            <div class="flex justify-between pt-2 border-t border-purple-200">
              <span class="font-bold">Итого к оплате:</span>
              <span class="font-bold text-lg text-purple-600">{{ dealData.total }}₽</span>
            </div>
          </div>
        </div>

        <!-- ✅ РЕЗУЛЬТАТ СПОРА (если есть) -->
        <div v-if="dealData.dispute_result" class="shrink-0">
          <div 
            :class="[
              'rounded-xl p-4 border-2',
              dealData.dispute_result.winner === 'client' ? 'bg-green-50 border-green-300' : 'bg-blue-50 border-blue-300'
            ]"
          >
            <div class="text-sm font-bold mb-2 flex items-center gap-2"
                 :class="dealData.dispute_result.winner === 'client' ? 'text-green-800' : 'text-blue-800'">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ dealData.dispute_result.message }}
            </div>
            <div class="text-xs" :class="dealData.dispute_result.winner === 'client' ? 'text-green-600' : 'text-blue-600'">
              {{ dealData.dispute_result.winner === 'client' ? 'Средства возвращены клиенту' : 'Средства выплачены исполнителю' }}
            </div>
          </div>
        </div>

        <!-- ✅ ИНФОРМАЦИЯ О СПОРЕ -->
        <div v-if="dealData.status === 'dispute'" class="shrink-0">
          <div class="bg-red-50 border border-red-200 rounded-xl p-4 mb-3">
            <div class="text-xs font-bold text-red-800 uppercase tracking-wider mb-2 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Претензия клиента
            </div>
            <div class="text-sm text-red-900 whitespace-pre-line leading-relaxed">{{ dealData.dispute_client_reason }}</div>
          </div>

          <div v-if="dealData.dispute_worker_defense" class="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-3">
            <div class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Защита исполнителя
            </div>
            <div class="text-sm text-blue-900 whitespace-pre-line leading-relaxed">{{ dealData.dispute_worker_defense }}</div>
          </div>

          <div v-if="dealData.is_dispute_pending_admin" class="bg-yellow-50 border border-yellow-200 rounded-xl p-3 text-sm text-yellow-800">
            <div class="font-bold mb-1 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Ожидает решения администратора
            </div>
            <div>Обе стороны представили свои аргументы. Решение принимает администратор.</div>
          </div>
        </div>

        <div v-if="dealData.revision_count > 0" class="shrink-0">
          <div class="bg-orange-50 border border-orange-200 rounded-xl p-3 text-sm">
            <span class="font-bold text-orange-800">Доработки: {{ dealData.revision_count }}/{{ dealData.max_revisions }}</span>
          </div>
        </div>

        <div v-if="dealData.status === 'delivered' && dealData.delivery_message" class="shrink-0">
          <div class="bg-green-50 border border-green-200 rounded-xl p-4">
            <div class="text-xs font-bold text-green-800 uppercase tracking-wider mb-2">Результат работы</div>
            <div class="text-sm text-green-900 whitespace-pre-line leading-relaxed">{{ dealData.delivery_message }}</div>
          </div>
        </div>
        
        <!-- ✅ ОБНОВЛЕННЫЙ БЛОК: Только ссылки на файлы, без превью изображений -->
        <div v-if="dealData.delivery_attachments && dealData.delivery_attachments.length > 0" class="shrink-0">
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2">Прикрепленные файлы</div>
            <div class="space-y-2">
              <a 
                v-for="att in dealData.delivery_attachments" 
                :key="att.id"
                :href="att.url" 
                :download="att.filename"
                class="flex items-center gap-2 p-2 rounded-lg bg-white hover:bg-blue-100 transition-all text-sm group"
              >
                <svg class="w-4 h-4 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                <span class="truncate text-blue-900 flex-1">{{ att.filename }}</span>
                <svg class="w-4 h-4 text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </a>
            </div>
          </div>
        </div>
        
        <div v-if="dealData.status === 'completed' && dealData.delivery_message" class="shrink-0">
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2">Работа завершена</div>
            <div class="text-sm text-blue-900 whitespace-pre-line leading-relaxed">{{ dealData.delivery_message }}</div>
          </div>
        </div>

        <!-- ✅ КНОПКИ ДЕЙСТВИЙ -->
        <div class="space-y-2 pb-2" :class="sidebarMode ? '' : 'mt-auto'">

          <button 
            v-if="showUpdatePriceButton"
            @click="showPriceModal = true"
            class="w-full border-2 border-blue-300 text-blue-600 py-2 rounded-xl font-bold hover:bg-blue-50 transition-all"
          >
            Изменить цену
          </button>

          <button 
            v-if="showPayButton"
            @click="payDeal"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
          >
            <span v-if="loading">Обработка...</span>
            <span v-else>Оплатить заказ ({{ dealData.total }}₽)</span>
          </button>

          <button 
            v-if="showDeliverButton"
            @click="showDeliveryModal = true"
            class="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
          >
            Сдать работу
          </button>

          <button 
            v-if="showCompleteButton"
            @click="showCompletionModal = true"
            class="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all"
          >
            Принять работу и завершить
          </button>

          <button 
            v-if="showRevisionButton"
            @click="showRevisionModal = true"
            class="w-full border-2 border-orange-300 text-orange-600 py-2 rounded-xl font-bold hover:bg-orange-50 transition-all"
          >
            Запросить доработку ({{ dealData.revision_count }}/{{ dealData.max_revisions }})
          </button>

          <!-- ✅ НОВАЯ КНОПКА: ОТКРЫТЬ СПОР (только для клиента после сдачи работы) -->
          <button 
            v-if="showOpenDisputeButton"
            @click="showDisputeModal = true"
            class="w-full border-2 border-red-300 text-red-600 py-2 rounded-xl font-bold hover:bg-red-50 transition-all flex items-center justify-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Открыть спор
          </button>

          <!-- ✅ КНОПКИ ДЛЯ ИСПОЛНИТЕЛЯ В СПОРЕ -->
          <button 
            v-if="showWorkerRefundButton"
            @click="workerRefund"
            :disabled="loading"
            class="w-full border-2 border-green-300 text-green-600 py-2 rounded-xl font-bold hover:bg-green-50 transition-all disabled:opacity-50"
          >
            <span v-if="loading">Обработка...</span>
            <span v-else>Вернуть деньги</span>
          </button>

          <button 
            v-if="showWorkerDefendButton"
            @click="showDefenseModal = true"
            class="w-full border-2 border-blue-300 text-blue-600 py-2 rounded-xl font-bold hover:bg-blue-50 transition-all"
          >
            Оспорить
          </button>

          <button 
            v-if="showCancelButton"
            @click="showCancelModal = true"
            class="w-full border-2 border-red-300 text-red-600 py-2 rounded-xl font-bold hover:bg-red-50 transition-all"
          >
            Отменить заказ
          </button>
        </div>

      </div>
    </div>

    <!-- МОДАЛЬНЫЕ ОКНА -->
    <teleport to="body">
      <!-- Изменение цены -->
      <div v-if="showPriceModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Изменить цену</h3>
          <p class="text-sm text-gray-600 mb-4">Клиент получит уведомление о новой цене.</p>
          
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2">Новая цена (₽)</label>
            <input 
              v-model="newPrice" 
              type="number" 
              min="1"
              class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Введите новую цену..."
            >
          </div>
          
          <div class="flex gap-3">
            <button @click="showPriceModal = false; newPrice = dealData.price" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="updatePrice" :disabled="loading || !newPrice || newPrice <= 0" class="flex-1 bg-blue-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Изменить</button>
          </div>
        </div>
      </div>

      <!-- Сдача работы -->
      <div v-if="showDeliveryModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Сдать работу</h3>
          <textarea 
            v-model="deliveryMessage" 
            rows="4"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4 text-sm"
            placeholder="Опишите что сделано, добавьте ссылки на результат..."
          ></textarea>
          <div class="mb-4">
  <label class="block text-sm font-bold mb-2">Прикрепить файлы (необязательно)</label>
  <label class="cursor-pointer">
    <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-blue-500 transition-all text-center">
      <svg class="w-8 h-8 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <span class="text-sm text-gray-600">Нажмите для выбора файлов</span>
    </div>
    <input 
      type="file" 
      multiple
      @change="handleDeliveryFileSelect"
      class="hidden"
    >
  </label>
  
  <div v-if="deliveryFiles.length > 0" class="mt-3 space-y-2">
    <div 
      v-for="(file, idx) in deliveryFiles" 
      :key="idx"
      class="flex items-center gap-2 px-3 py-2 bg-blue-50 rounded-lg"
    >
      <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <span class="flex-1 text-sm truncate">{{ file.name }}</span>
      <button @click="removeDeliveryFile(idx)" class="text-red-500 hover:text-red-700">×</button>
    </div>
  </div>
</div>
          <div class="flex gap-3">
            <button @click="showDeliveryModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="deliverWork" :disabled="!deliveryMessage.trim() || loading" class="flex-1 bg-blue-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Сдать</button>
          </div>
        </div>
      </div>

      <!-- Завершение с отзывом -->
      <div v-if="showCompletionModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl text-center">
          <h3 class="text-xl font-bold mb-4">Принять работу?</h3>
          <p class="text-sm text-gray-600 mb-6">После принятия деньги будут переведены исполнителю.</p>
          
          <div class="mb-6">
            <label class="block text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Оценка работы</label>
            <div class="flex gap-3 justify-center">
              <button 
                v-for="star in 5" 
                :key="star"
                @click="rating = star"
                class="transition-transform hover:scale-125 focus:outline-none"
              >
                <svg 
                   class="w-8 h-8" 
                   :class="star <= rating ? 'text-yellow-400' : 'text-gray-200'"
                   viewBox="0 0 24 24" 
                   fill="currentColor"
                >
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </button>
            </div>
          </div>
          
          <textarea 
            v-model="completionMessage" 
            rows="3"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-green-500 mb-4 text-sm"
            placeholder="Ваш отзыв..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showCompletionModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="completeDeal" :disabled="loading || rating === 0" class="flex-1 bg-green-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Принять</button>
          </div>
        </div>
      </div>

      <!-- Доработка -->
      <div v-if="showRevisionModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-4">Запросить доработку</h3>
          <p class="text-sm text-gray-600 mb-4">Осталось бесплатных доработок: {{ dealData.max_revisions - dealData.revision_count }}</p>
          <textarea 
            v-model="revisionReason" 
            rows="4"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-orange-500 mb-4 text-sm"
            placeholder="Опишите что нужно доработать..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showRevisionModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="requestRevision" :disabled="!revisionReason.trim() || loading" class="flex-1 bg-orange-500 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Запросить</button>
          </div>
        </div>
      </div>

      <!-- ✅ МОДАЛЬНОЕ ОКНО: ОТКРЫТЬ СПОР -->
      <div v-if="showDisputeModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-2 text-red-600">Открыть спор</h3>
          <p class="text-sm text-gray-600 mb-4">Опишите, что не так с выполненной работой. Исполнитель сможет вернуть деньги или оспорить вашу претензию.</p>
          <textarea 
            v-model="disputeReason" 
            rows="5"
            class="w-full p-3 rounded-xl border border-red-200 resize-none focus:outline-none focus:ring-2 focus:ring-red-500 mb-4 text-sm"
            placeholder="Подробно опишите проблему..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showDisputeModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="openDispute" :disabled="!disputeReason.trim() || loading" class="flex-1 bg-red-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Открыть спор</button>
          </div>
        </div>
      </div>

      <!-- ✅ МОДАЛЬНОЕ ОКНО: ЗАЩИТА ИСПОЛНИТЕЛЯ -->
      <div v-if="showDefenseModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold mb-2 text-blue-600">Оспорить претензию</h3>
          <p class="text-sm text-gray-600 mb-4">Представьте свои аргументы. После отправки спор будет передан администратору для принятия решения.</p>
          <textarea 
            v-model="defenseText" 
            rows="5"
            class="w-full p-3 rounded-xl border border-blue-200 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4 text-sm"
            placeholder="Объясните, почему претензия необоснована..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showDefenseModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Отмена</button>
            <button @click="workerDefend" :disabled="!defenseText.trim() || loading" class="flex-1 bg-blue-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Отправить</button>
          </div>
        </div>
      </div>

      <!-- Отмена заказа -->
      <div v-if="showCancelModal" class="fixed inset-0 bg-black/40 z-[300] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl text-center">
          <h3 class="text-xl font-bold mb-2 text-red-600">Отменить заказ?</h3>
          <p class="text-sm text-gray-600 mb-4" v-if="dealData.status === 'paid'">Средства будут возвращены клиенту.</p>
          <textarea 
            v-model="cancelReason" 
            rows="3"
            class="w-full p-3 rounded-xl border border-gray-200 resize-none focus:outline-none focus:ring-2 focus:ring-red-500 mb-4 text-sm"
            placeholder="Причина отмены..."
          ></textarea>
          <div class="flex gap-3">
            <button @click="showCancelModal = false" class="flex-1 border-2 py-2 rounded-lg text-sm font-bold">Назад</button>
            <button @click="cancelDeal" :disabled="loading" class="flex-1 bg-red-600 text-white py-2 rounded-lg font-bold disabled:opacity-50 text-sm">Отменить</button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
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

// ✅ ИСПРАВЛЕНИЕ: Правильно определяем ID заказа
const dealId = computed(() => {
  return props.dealData.id || 
         props.dealData.deal_id || 
         props.message?.deal_id ||
         props.message?.id
})

// Модалки
const showDeliveryModal = ref(false)
const showCompletionModal = ref(false)
const showRevisionModal = ref(false)
const showCancelModal = ref(false)
const showPriceModal = ref(false)
const showDisputeModal = ref(false)
const showDefenseModal = ref(false)

// Сообщения
const deliveryMessage = ref('')
const completionMessage = ref('')
const revisionReason = ref('')
const cancelReason = ref('')
const rating = ref(0)
const newPrice = ref(props.dealData.price)
const disputeReason = ref('')
const defenseText = ref('')

// Проверки роли
const isClient = computed(() => String(auth.user.id) === String(props.dealData.client_id))
const isWorker = computed(() => String(auth.user.id) === String(props.dealData.worker_id))

// Стили статуса
const borderColor = computed(() => {
  const colors = {
    'pending': 'border-purple-300',
    'paid': 'border-blue-300',
    'delivered': 'border-green-300',
    'dispute': 'border-red-300',
    'completed': 'border-orange-300',
    'cancelled': 'border-gray-300',
  }
  return colors[props.dealData.status] || 'border-gray-200'
})

const statusIconBg = computed(() => {
  const bgs = {
    'pending': 'bg-gradient-to-br from-purple-400 to-purple-600',
    'paid': 'bg-gradient-to-br from-blue-400 to-blue-600',
    'delivered': 'bg-gradient-to-br from-green-400 to-green-600',
    'dispute': 'bg-gradient-to-br from-red-400 to-red-600',
    'completed': 'bg-gradient-to-br from-orange-400 to-orange-600',
    'cancelled': 'bg-gradient-to-br from-gray-400 to-gray-600',
  }
  return bgs[props.dealData.status] || 'bg-gray-500'
})

const statusLabel = computed(() => {
  // ✅ Если есть результат спора - показываем его
  if (props.dealData.dispute_result) {
    const winner = props.dealData.dispute_result.winner_text
    if (props.dealData.status === 'cancelled') {
      return `Отменён (спор - победа ${winner})`
    }
    if (props.dealData.status === 'completed') {
      return `Завершён (спор - победа ${winner})`
    }
  }
  
  // Обычные статусы
  const labels = {
    'pending': 'Ожидает оплаты',
    'paid': 'В работе',
    'delivered': 'На проверке',
    'dispute': 'В споре',
    'completed': 'Завершен',
    'cancelled': 'Отменен',
  }
  return labels[props.dealData.status] || props.dealData.status
})

const statusTextColor = computed(() => {
  const colors = {
    'pending': 'text-purple-600',
    'paid': 'text-blue-600',
    'delivered': 'text-green-600',
    'dispute': 'text-red-600',
    'completed': 'text-orange-600',
    'cancelled': 'text-gray-600',
  }
  return colors[props.dealData.status] || 'text-gray-600'
})

// Показываем кнопки
const showPayButton = computed(() => {
  return isClient.value && props.dealData.can_pay
})

const showDeliverButton = computed(() => {
  return isWorker.value && props.dealData.can_deliver
})

const showCompleteButton = computed(() => {
  return isClient.value && props.dealData.can_complete
})

const showRevisionButton = computed(() => {
  return isClient.value && props.dealData.can_request_revision
})

const showCancelButton = computed(() => {
  return props.dealData.can_cancel
})

const showUpdatePriceButton = computed(() => {
  return isWorker.value && props.dealData.can_update_price
})

const showOpenDisputeButton = computed(() => {
  return isClient.value && props.dealData.can_open_dispute
})

const showWorkerRefundButton = computed(() => {
  return isWorker.value && props.dealData.can_worker_refund
})

const showWorkerDefendButton = computed(() => {
  return isWorker.value && props.dealData.can_worker_defend
})

// ДЕЙСТВИЯ
const updatePrice = async () => {
  loading.value = true
  try {
    await axios.patch(`/api/market/deals/${dealId.value}/update-price/`, {
      price: newPrice.value
    })
    showPriceModal.value = false
    emit('deal-action')
  } catch (e) {
    alert('Ошибка изменения цены: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const payDeal = async () => {
  if (!confirm(`Оплатить заказ на сумму ${props.dealData.total}₽?`)) return
  
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/pay/`)
    emit('deal-action')
  } catch (e) {
    alert('Ошибка оплаты: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}

const deliverWork = async () => {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('delivery_message', deliveryMessage.value)
    
    deliveryFiles.value.forEach(file => {
      formData.append('files', file)
    })
    
    await axios.post(`/api/market/deals/${dealId.value}/deliver/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
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

const completeDeal = async () => {
  if (rating.value === 0) {
    alert('Пожалуйста, поставьте оценку')
    return
  }
  
  loading.value = true
  try {
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
const deliveryFiles = ref([])

const handleDeliveryFileSelect = (event) => {
  const files = Array.from(event.target.files)
  
  const validFiles = files.filter(file => {
    if (file.size > 20 * 1024 * 1024) {
      alert(`Файл ${file.name} слишком большой (макс 20MB)`)
      return false
    }
    return true
  })
  
  deliveryFiles.value.push(...validFiles)
  event.target.value = ''
}

const removeDeliveryFile = (index) => {
  deliveryFiles.value.splice(index, 1)
}

const requestRevision = async () => {
  loading.value = true
  try {
    await axios.post(`/api/market/deals/${dealId.value}/revision/`, {
      revision_reason: revisionReason.value
    })
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
    await axios.post(`/api/market/deals/${dealId.value}/open-dispute/`, {
      dispute_reason: disputeReason.value
    })
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
    await axios.post(`/api/market/deals/${dealId.value}/worker-defend/`, {
      defense_text: defenseText.value
    })
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
    await axios.post(`/api/market/deals/${dealId.value}/cancel/`, {
      reason: cancelReason.value || 'Не указана'
    })
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

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(112, 0, 255, 0.3);
  border-radius: 10px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgba(112, 0, 255, 0.5);
}
</style>
