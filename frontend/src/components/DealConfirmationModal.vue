<template>
  <div v-if="show" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in">
    <div class="bg-white rounded-[32px] p-8 max-w-2xl w-full shadow-2xl relative border border-white/50 max-h-[90vh] overflow-y-auto">
      
      <button 
        @click="$emit('close')" 
        class="absolute top-6 right-6 w-8 h-8 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-900 transition-all flex items-center justify-center"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div v-if="step === 1">
        <div class="flex items-center gap-4 mb-8">
          <div class="w-12 h-12 rounded-2xl bg-[#7000ff]/10 flex items-center justify-center text-[#7000ff]">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h2 class="text-2xl font-extrabold text-[#1a1a2e] tracking-tight">Предложить сделку</h2>
            <p class="text-sm text-gray-400 font-medium">Безопасная сделка через сервис</p>
          </div>
        </div>

        <div class="bg-gray-50 rounded-2xl p-6 mb-6 border border-gray-100">
          <div class="flex items-center gap-2 mb-3">
            <svg class="w-4 h-4 text-[#7000ff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 class="font-bold text-[13px] uppercase tracking-wider text-gray-500">Техническое задание</h3>
          </div>
          <div class="prose prose-sm max-w-none text-gray-600 whitespace-pre-line max-h-[250px] overflow-y-auto leading-relaxed pr-2 custom-scrollbar">
            {{ order.agreed_tz }}
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div class="bg-[#1a1a2e] rounded-2xl p-5 text-white shadow-lg shadow-[#1a1a2e]/10">
            <div class="text-[10px] uppercase tracking-[0.1em] text-gray-400 font-bold mb-3">Финансовые условия</div>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">Сумма:</span>
                <span class="font-mono">{{ order.price }} ₽</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">Комиссия (8%):</span>
                <span class="font-mono">{{ commission }} ₽</span>
              </div>
              <div class="pt-2 border-t border-white/10 flex justify-between items-end">
                <span class="text-xs font-bold uppercase text-[#7000ff]">Итого</span>
                <span class="text-xl font-bold font-mono">{{ total }} ₽</span>
              </div>
            </div>
          </div>

          <div class="bg-white border border-gray-100 rounded-2xl p-5">
            <div class="text-[10px] uppercase tracking-[0.1em] text-gray-400 font-bold mb-3">Статус согласия</div>
            <div class="space-y-3">
              <div class="flex items-center gap-3">
                <div :class="order.client_confirmed ? 'bg-green-500' : 'bg-gray-200'" class="w-2 h-2 rounded-full shadow-sm"></div>
                <span class="text-xs font-bold" :class="order.client_confirmed ? 'text-gray-900' : 'text-gray-400'">
                  {{ order.client_confirmed ? 'Заказчик подтвердил' : 'Ожидание заказчика' }}
                </span>
              </div>
              <div class="flex items-center gap-3">
                <div :class="order.worker_confirmed ? 'bg-green-500' : 'bg-gray-200'" class="w-2 h-2 rounded-full shadow-sm"></div>
                <span class="text-xs font-bold" :class="order.worker_confirmed ? 'text-gray-900' : 'text-gray-400'">
                  {{ order.worker_confirmed ? 'Исполнитель подтвердил' : 'Ожидание исполнителя' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex gap-4">
          <button 
            @click="$emit('close')" 
            class="flex-1 px-6 py-4 rounded-2xl text-sm font-bold text-gray-500 hover:text-gray-800 hover:bg-gray-50 transition-all uppercase tracking-widest"
          >
            Отмена
          </button>
          <button 
            @click="proposeDeal" 
            :disabled="loading"
            class="flex-[2] bg-[#7000ff] hover:bg-[#5b00d1] text-white py-4 rounded-2xl shadow-xl shadow-[#7000ff]/20 hover:shadow-[#7000ff]/30 active:scale-[0.98] transition-all font-bold uppercase tracking-widest text-sm disabled:opacity-50"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Обработка...
            </span>
            <span v-else>Подтвердить условия</span>
          </button>
        </div>
      </div>

      <div v-if="step === 2">
        <div class="text-center py-10">
          <div class="w-20 h-20 rounded-[24px] bg-green-50 flex items-center justify-center mx-auto mb-6">
            <svg class="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 class="text-2xl font-extrabold text-[#1a1a2e] mb-2 tracking-tight">Сделка активирована</h3>
          <p class="text-gray-500 mb-8 font-medium leading-relaxed">{{ successMessage }}</p>
          
          <button 
            @click="$emit('close'); $router.push('/chats')" 
            class="bg-[#1a1a2e] hover:bg-black text-white px-10 py-4 rounded-2xl font-bold uppercase tracking-widest text-xs transition-all shadow-lg shadow-black/10"
          >
            Вернуться в чат
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
background: #e5e7eb;
border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
background: #d1d5db;
}

@keyframes fade-in {
from { opacity: 0; transform: translateY(10px); }
to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
animation: fade-in 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
</style>
