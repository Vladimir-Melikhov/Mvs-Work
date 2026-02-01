<template>
  <div class="hidden md:flex h-[calc(100vh-150px)] gap-4 max-w-7xl mx-auto pt-4 pb-2 px-4">
    
    <div class="flex-1 flex flex-col min-w-0">
      
      <div class="glass px-6 py-3 rounded-[24px] flex items-center gap-4 mb-3 border border-white/60 shadow-sm shrink-0">
        <button 
          @click="$router.push('/chats')" 
          class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold"
        >
          ←
        </button>
        
        <div 
          class="cursor-pointer hover:ring-2 hover:ring-[#7000ff] rounded-full transition-all"
          @click="goToPartnerProfile"
        >
          <UserAvatar 
            :avatar-url="partner?.avatar"
            :name="partner?.name || 'U'"
            size="lg"
            class="ring-2 ring-white/50 shadow-md"
          />
        </div>
        
        <div class="flex-1">
          <h2 
            class="text-lg font-bold text-[#1a1a2e] cursor-pointer hover:text-[#7000ff] transition-colors"
            @click="goToPartnerProfile"
          >
            {{ partner ? partner.name : 'Загрузка...' }}
          </h2>
        </div>

        <TelegramNotificationBanner />
      </div>

      <div 
        ref="messagesContainer"
        class="flex-1 glass rounded-[32px] p-6 overflow-y-auto mb-3 border border-white/40"
      >
        <div v-if="loading" class="text-center py-10 opacity-50 flex justify-center">
          <div class="w-6 h-6 border-2 border-[#7000ff] border-t-transparent rounded-full animate-spin"></div>
        </div>

        <div v-else-if="textMessages.length === 0" class="text-center py-20 text-gray-400">
          <div class="text-5xl mb-3 opacity-30">👋</div>
          <p class="text-sm font-medium">Начните диалог</p>
        </div>

        <template v-else>
          <div v-for="(group, index) in groupedMessages" :key="index">
            <div class="flex items-center justify-center my-6">
              <div class="px-4 py-1.5 rounded-full bg-white/60 border border-white/80 shadow-sm">
                <span class="text-xs font-bold text-gray-600">{{ group.date }}</span>
              </div>
            </div>

            <div 
              v-for="msg in group.messages" 
              :key="msg.id" 
              class="animate-scale-in flex flex-col mb-4"
              :class="isMyMessage(msg) ? 'items-end' : 'items-start'"
            >
              <div 
                class="max-w-[75%] px-5 py-3 text-[15px] leading-relaxed shadow-sm break-words"
                :class="isMyMessage(msg) 
                  ? 'bg-[#1a1a2e] text-white rounded-[22px] rounded-br-none' 
                  : 'bg-white text-[#1a1a2e] rounded-[22px] rounded-bl-none border border-white/60'"
              >
                <div 
                  class="whitespace-pre-wrap" 
                  v-html="formatMessageText(msg.text, ['📋', '💰', '💳', '📦', '🔄', '⚠️', '🛡️', '🎉', '❌'].some(m => msg.text.startsWith(m)))"
                ></div>
                
                <div v-if="msg.attachments && msg.attachments.length > 0" class="mt-2 space-y-2">
                  <div 
                    v-for="(att, idx) in msg.attachments" 
                    :key="idx"
                  >
                    <img 
                      v-if="att.content_type?.startsWith('image/') && att.display_mode !== 'attachment'"
                      :src="att.url" 
                      :alt="att.name || att.filename"
                      class="max-w-full max-h-96 rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                      @click="window.open(att.url, '_blank')"
                    />
                    
                    <a 
                      v-else
                      :href="att.url" 
                      target="_blank"
                      class="flex items-center gap-2 p-3 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-sm group cursor-pointer"
                    >
                      <div class="w-8 h-8 rounded bg-white/20 flex items-center justify-center shrink-0">
                        <svg v-if="att.content_type?.startsWith('image/')" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      
                      <div class="flex-1 min-w-0">
                        <div class="font-medium truncate">{{ att.name || att.filename }}</div>
                        <div class="text-xs opacity-60 flex items-center gap-2">
                          <span>{{ formatFileSize(att.size || att.file_size) }}</span>
                          <span v-if="att.content_type?.startsWith('image/')" class="text-blue-400">• Изображение</span>
                        </div>
                      </div>
                      
                      <div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </div>
                    </a>
                  </div>
                </div>
                
                <div 
                  class="text-[10px] mt-1.5 font-medium opacity-60 text-right"
                  :class="isMyMessage(msg) ? 'text-white/60' : 'text-gray-400'"
                >
                  {{ formatTime(msg.created_at) }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="glass p-2 rounded-[26px] flex items-center gap-2 border border-white/60 shadow-xl bg-white/40 backdrop-blur-xl shrink-0">
        <label class="cursor-pointer w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/40 transition-all" title="Отправить изображение (сжатое)">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <input 
            type="file" 
            multiple
            @change="handleImageSelect"
            class="hidden"
            accept="image/*"
          >
        </label>
        
        <label class="cursor-pointer w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/40 transition-all" title="Прикрепить файл (без сжатия)">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <input 
            type="file" 
            multiple
            @change="handleFileSelect"
            class="hidden"
          >
        </label>
        
        <input 
          v-model="newMessage" 
          @keydown.enter="sendMessage"
          type="text" 
          placeholder="Напишите сообщение..." 
          class="flex-1 bg-transparent border-none outline-none px-6 py-3.5 text-[#1a1a2e] placeholder-gray-500 font-medium text-[15px]"
        >
        <button 
          @click="sendMessage"
          :disabled="(!newMessage.trim() && selectedFiles.length === 0) || !isConnected || uploading"
          class="w-12 h-12 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] hover:scale-105 transition-all disabled:opacity-50"
        >
          <svg v-if="!uploading" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          <div v-else class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </div>
      
      <div v-if="selectedFiles.length > 0" class="mt-2 flex flex-wrap gap-2">
        <div 
          v-for="(file, idx) in selectedFiles" 
          :key="idx"
          class="flex items-center gap-2 px-3 py-1 bg-white/60 rounded-full text-sm"
        >
          <span class="truncate max-w-[150px]">{{ file.name }}</span>
          <button @click="removeFile(idx)" class="text-red-500 hover:text-red-700">×</button>
        </div>
      </div>
    </div>

    <!-- Sidebar с адаптивной шириной -->
    <div class="w-80 lg:w-96 shrink-0 overflow-y-auto pr-2 scrollbar-thin">
      <div class="mb-4">
        <a 
          :href="supportLink" 
          target="_blank"
          rel="noopener noreferrer"
          class="glass flex items-center gap-3 p-4 rounded-[24px] border border-white/40 hover:bg-white/20 transition-all group"
        >
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#7000ff] to-[#5500cc] flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-bold text-[#1a1a2e] group-hover:text-[#7000ff] transition-colors">
              Служба поддержки
            </div>
            <div class="text-xs text-gray-500">Нужна помощь? Напишите нам</div>
          </div>
          <svg class="w-4 h-4 text-gray-400 group-hover:text-[#7000ff] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
      
      <div v-if="activeDeals.length === 0" class="glass rounded-[32px] p-6 border border-white/40 flex flex-col items-center justify-center text-center min-h-[300px]">
        <div class="text-5xl mb-3 opacity-30">📋</div>
        <p class="text-sm text-gray-500 mb-4">Заказов пока нет</p>
      </div>

      <div v-else class="space-y-3 pb-4">
        <div 
          v-for="(deal, index) in activeDeals" 
          :key="deal.deal_id"
          class="glass rounded-[24px] border border-white/40 overflow-hidden"
        >
          <div 
            @click="toggleDeal(index)"
            class="p-4 cursor-pointer hover:bg-white/20 transition-all flex items-center justify-between"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-bold text-[#1a1a2e] truncate">{{ deal.title }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ getStatusLabel(deal.status) }}</div>
            </div>
            <div class="flex items-center gap-2">
              <div class="text-[#7000ff] font-bold text-sm">{{ deal.price }}₽</div>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-5 w-5 text-gray-400 transition-transform"
                :class="expandedDealIndex === index ? 'rotate-180' : ''"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div 
            v-if="expandedDealIndex === index"
            class="border-t border-white/20"
          >
            <DealMessage 
              :message="dealMessages.find(m => m.deal_data?.deal_id === deal.deal_id)"
              :deal-data="deal"
              @deal-action="refreshMessages"
              sidebar-mode
            />
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- MOBILE VERSION -->
  <div class="md:hidden flex flex-col" style="height: 100vh; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: #f2f4f8;">
    
    <div class="glass px-3 py-2 rounded-b-[24px] flex items-center gap-2 border-b border-white/60 shadow-sm shrink-0">
      <button 
        @click="$router.push('/chats')" 
        class="w-9 h-9 flex items-center justify-center rounded-full bg-white/40 hover:bg-white/80 text-[#1a1a2e] transition-all font-bold"
      >
        ←
      </button>
      
      <div class="cursor-pointer" @click="goToPartnerProfile">
        <UserAvatar 
          :avatar-url="partner?.avatar"
          :name="partner?.name || 'U'"
          size="sm"
          class="ring-2 ring-white/50 shadow-md"
        />
      </div>
      
      <div class="flex-1 min-w-0">
        <h2 
          class="text-sm font-bold text-[#1a1a2e] truncate cursor-pointer"
          @click="goToPartnerProfile"
        >
          {{ partner ? partner.name : 'Загрузка...' }}
        </h2>
      </div>

      <button 
        v-if="activeDeals.length > 0"
        @click="mobileShowDeal = !mobileShowDeal"
        class="w-9 h-9 flex items-center justify-center rounded-full transition-all font-bold relative"
        :class="mobileShowDeal ? 'bg-[#7000ff] text-white' : 'bg-white/40 text-[#1a1a2e]'"
      >
        📋
        <span v-if="activeDeals.length > 1" class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {{ activeDeals.length }}
        </span>
      </button>
      
      <button 
        @click="mobileShowHelp = !mobileShowHelp"
        class="w-9 h-9 flex items-center justify-center rounded-full transition-all font-bold"
        :class="mobileShowHelp ? 'bg-[#7000ff] text-white' : 'bg-white/40 text-[#1a1a2e]'"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    </div>

    <div v-if="mobileShowHelp" class="p-3 shrink-0 space-y-2">
      <a 
        :href="supportLink" 
        target="_blank"
        rel="noopener noreferrer"
        class="glass flex items-center gap-3 p-3 rounded-[20px] border border-white/40 hover:bg-white/20 transition-all"
      >
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-[#7000ff] to-[#5500cc] flex items-center justify-center shrink-0">
          <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-bold text-[#1a1a2e]">Служба поддержки</div>
          <div class="text-xs text-gray-500">Нужна помощь? Напишите нам</div>
        </div>
      </a>
      
      <TelegramNotificationBanner />
    </div>

    <div v-if="!mobileShowDeal" class="flex-1 flex flex-col min-h-0 px-2">
      <div 
        ref="mobileMessagesContainer"
        class="flex-1 glass rounded-[28px] p-3 overflow-y-auto my-2 border border-white/40"
      >
        <div v-if="loading" class="text-center py-10 opacity-50 flex justify-center">
          <div class="w-6 h-6 border-2 border-[#7000ff] border-t-transparent rounded-full animate-spin"></div>
        </div>

        <div v-else-if="textMessages.length === 0" class="text-center py-20 text-gray-400">
          <div class="text-5xl mb-3 opacity-30">👋</div>
          <p class="text-sm font-medium">Начните диалог</p>
        </div>

        <template v-else>
          <div v-for="(group, index) in groupedMessages" :key="index">
            <div class="flex items-center justify-center my-4">
              <div class="px-3 py-1 rounded-full bg-white/60 border border-white/80 shadow-sm">
                <span class="text-[10px] font-bold text-gray-600">{{ group.date }}</span>
              </div>
            </div>

            <div 
              v-for="msg in group.messages" 
              :key="msg.id" 
              class="animate-scale-in flex flex-col mb-2"
              :class="isMyMessage(msg) ? 'items-end' : 'items-start'"
            >
              <div 
                class="max-w-[85%] px-3 py-2 text-sm leading-relaxed shadow-sm break-words"
                :class="isMyMessage(msg) 
                  ? 'bg-[#1a1a2e] text-white rounded-[18px] rounded-br-none' 
                  : 'bg-white text-[#1a1a2e] rounded-[18px] rounded-bl-none border border-white/60'"
              >
                <div 
                  class="whitespace-pre-wrap" 
                  v-html="formatMessageText(msg.text, ['📋', '💰', '💳', '📦', '🔄', '⚠️', '🛡️', '🎉', '❌'].some(m => msg.text.startsWith(m)))"
                ></div>
                
                <div v-if="msg.attachments && msg.attachments.length > 0" class="mt-2 space-y-1">
                  <div 
                    v-for="(att, idx) in msg.attachments" 
                    :key="idx"
                  >
                    <img 
                      v-if="att.content_type?.startsWith('image/') && att.display_mode !== 'attachment'"
                      :src="att.url" 
                      :alt="att.name || att.filename"
                      class="max-w-full max-h-64 rounded-lg cursor-pointer"
                      @click="window.open(att.url, '_blank')"
                    />
                    
                    <a 
                      v-else
                      :href="att.url" 
                      target="_blank"
                      class="flex items-center gap-2 p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-xs group"
                    >
                      <div class="w-6 h-6 rounded bg-white/20 flex items-center justify-center shrink-0">
                        <svg v-if="att.content_type?.startsWith('image/')" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      
                      <div class="flex-1 min-w-0">
                        <div class="font-medium truncate text-xs">{{ att.name || att.filename }}</div>
                        <div class="text-[10px] opacity-60">{{ formatFileSize(att.size || att.file_size) }}</div>
                      </div>
                      
                      <svg class="w-4 h-4 opacity-0 group-hover:opacity-100 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>
                
                <div 
                  class="text-[9px] mt-1 font-medium opacity-60 text-right"
                  :class="isMyMessage(msg) ? 'text-white/60' : 'text-gray-400'"
                >
                  {{ formatTime(msg.created_at) }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="glass p-1.5 rounded-[22px] flex items-center gap-1.5 border border-white/60 shadow-xl bg-white/40 backdrop-blur-xl shrink-0 mb-2">
        <label class="cursor-pointer w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/40 transition-all shrink-0" title="Изображение (сжатое)">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <input 
            type="file" 
            multiple
            @change="handleImageSelect"
            class="hidden"
            accept="image/*"
          >
        </label>
        
        <label class="cursor-pointer w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/40 transition-all shrink-0" title="Файл (без сжатия)">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <input 
            type="file" 
            multiple
            @change="handleFileSelect"
            class="hidden"
          >
        </label>
        
        <input 
          v-model="newMessage" 
          @keydown.enter="sendMessage"
          type="text" 
          placeholder="Сообщение..." 
          class="flex-1 bg-transparent border-none outline-none px-3 py-2.5 text-[#1a1a2e] placeholder-gray-500 font-medium text-sm min-w-0"
        >
        <button 
          @click="sendMessage"
          :disabled="(!newMessage.trim() && selectedFiles.length === 0) || !isConnected || uploading"
          class="w-9 h-9 bg-[#1a1a2e] rounded-full flex items-center justify-center text-white shadow-lg hover:bg-[#7000ff] transition-all disabled:opacity-50 shrink-0"
        >
          <svg v-if="!uploading" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          <div v-else class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </div>
      
      <div v-if="selectedFiles.length > 0" class="mb-2 flex flex-wrap gap-1">
        <div 
          v-for="(file, idx) in selectedFiles" 
          :key="idx"
          class="flex items-center gap-1 px-2 py-1 bg-white/60 rounded-full text-xs"
        >
          <span class="truncate max-w-[100px]">{{ file.name }}</span>
          <button @click="removeFile(idx)" class="text-red-500 hover:text-red-700 text-sm">×</button>
        </div>
      </div>
    </div>

    <div v-else class="flex-1 overflow-y-auto p-2">
      <div v-if="activeDeals.length === 0" class="glass rounded-[32px] p-6 border border-white/40 flex flex-col items-center justify-center text-center h-full">
        <div class="text-5xl mb-3 opacity-30">📋</div>
        <p class="text-sm text-gray-500 mb-4">Заказов пока нет</p>
      </div>

      <div v-else class="space-y-2">
        <div 
          v-for="(deal, index) in activeDeals" 
          :key="deal.deal_id"
          class="glass rounded-[24px] border border-white/40 overflow-hidden"
        >
          <div 
            @click="toggleDeal(index)"
            class="p-3 cursor-pointer hover:bg-white/20 transition-all flex items-center justify-between"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-bold text-[#1a1a2e] truncate">{{ deal.title }}</div>
              <div class="text-xs text-gray-500 mt-1">{{ getStatusLabel(deal.status) }}</div>
            </div>
            <div class="flex items-center gap-2">
              <div class="text-[#7000ff] font-bold text-sm">{{ deal.price }}₽</div>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-5 w-5 text-gray-400 transition-transform"
                :class="expandedDealIndex === index ? 'rotate-180' : ''"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div 
            v-if="expandedDealIndex === index"
            class="border-t border-white/20"
          >
            <DealMessage 
              :message="dealMessages.find(m => m.deal_data?.deal_id === deal.deal_id)"
              :deal-data="deal"
              @deal-action="refreshMessages"
              sidebar-mode
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import axios from 'axios'
import DealMessage from '../components/DealMessage.vue'
import UserAvatar from '../components/UserAvatar.vue'
import TelegramNotificationBanner from '../components/TelegramNotificationBanner.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const messagesContainer = ref(null)
const mobileMessagesContainer = ref(null)
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const isConnected = ref(false)
const partner = ref(null)
const mobileShowDeal = ref(false)
const mobileShowHelp = ref(false)
const expandedDealIndex = ref(0)
const selectedFiles = ref([])
const uploading = ref(false)

let socket = null
const roomId = route.params.id

const supportLink = computed(() => {
  const botUsername = import.meta.env.VITE_SUPPORT_BOT_USERNAME || 'your_support_bot'
  return `https://t.me/${botUsername}`
})

const textMessages = computed(() => {
  return messages.value.filter(m => m.message_type === 'text')
})

const dealMessages = computed(() => {
  return messages.value.filter(m => m.message_type !== 'text')
})

const activeDeals = computed(() => {
  return dealMessages.value
    .map(m => m.deal_data)
    .filter(d => d && d.deal_id)
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
})

const groupedMessages = computed(() => {
  const groups = []
  let currentDate = null
  let currentGroup = null

  textMessages.value.forEach(msg => {
    const msgDate = new Date(msg.created_at)
    const dateKey = formatDateKey(msgDate)

    if (dateKey !== currentDate) {
      if (currentGroup) {
        groups.push(currentGroup)
      }
      currentDate = dateKey
      currentGroup = {
        date: formatDateLabel(msgDate),
        messages: []
      }
    }

    currentGroup.messages.push(msg)
  })

  if (currentGroup) {
    groups.push(currentGroup)
  }

  return groups
})

const formatDateKey = (date) => {
  return date.toISOString().split('T')[0]
}

const formatDateLabel = (date) => {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const isToday = formatDateKey(date) === formatDateKey(today)
  const isYesterday = formatDateKey(date) === formatDateKey(yesterday)

  if (isToday) return 'Сегодня'
  if (isYesterday) return 'Вчера'

  const options = { day: 'numeric', month: 'long' }
  return date.toLocaleDateString('ru-RU', options)
}

const isMyMessage = (msg) => String(msg.sender_id) === String(auth.user.id)
const formatTime = (isoString) => new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const formatFileSize = (bytes) => {
  if (bytes === undefined || bytes === null || isNaN(bytes)) return ''; 
  
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatMessageText = (text, isSystem = false) => {
  if (!text) return ''
  if (!isSystem) return text
  
  const emojiMap = {
    '💰': { type: 'ruble', color: 'purple' },
    '💳': { type: 'ruble', color: 'purple' },
    '✅': { type: 'check', color: 'success' },
    '📦': { type: 'work', color: 'info' },
    '🔄': { type: 'clock', color: 'warning' },
    '🎉': { type: 'check', color: 'success' },
    '❌': { type: 'cancel', color: 'error' },
    '⚠️': { type: 'warning', color: 'warning' },
    '⏳': { type: 'clock', color: 'default' },
    '⚡': { type: 'lightning', color: 'purple' },
    '📋': { type: 'document', color: 'info' },
    '🛡️': { type: 'info', color: 'info' }
  }
  
  let formatted = text
  Object.entries(emojiMap).forEach(([emoji, config]) => {
    const iconSvg = `<span class="inline-flex items-center align-middle mx-1">
      <svg class="w-5 h-5 ${getColorClass(config.color)}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        ${getIconPath(config.type)}
      </svg>
    </span>`
    formatted = formatted.replaceAll(emoji, iconSvg)
  })
  return formatted
}

const getColorClass = (color) => {
  const classes = { success: 'text-green-600', error: 'text-red-600', warning: 'text-orange-600', info: 'text-blue-600', purple: 'text-purple-600', default: 'text-gray-600' }
  return classes[color] || classes.default
}

const getIconPath = (type) => {
  const paths = {
    money: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v12M8 9h8M8 15h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    ruble: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M9 7h4.5c1.38 0 2.5 1.12 2.5 2.5S14.88 12 13.5 12H9M9 7v12M7 14h5M9 12h4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    check: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M8 12l3 3 5-6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>',
    work: '<path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    cancel: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    warning: '<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    clock: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    lightning: '<path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>',
    document: '<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    info: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 16v-4m0-4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
  }
  return paths[type] || paths.info
}

const getStatusLabel = (status) => {
  const labels = { 'pending': 'Ожидает оплаты', 'paid': 'В работе', 'delivered': 'Сдано', 'completed': 'Завершено', 'cancelled': 'Отменено' }
  return labels[status] || status
}

const toggleDeal = (index) => { expandedDealIndex.value = expandedDealIndex.value === index ? null : index }

const goToPartnerProfile = () => {
  const partnerId = partner.value?.id
  if (partnerId) router.push(`/users/${partnerId}`)
}

const handleImageSelect = async (event) => {
  const files = Array.from(event.target.files)
  
  if (files.length === 0) return
  
  uploading.value = true
  
  try {
    for (const file of files) {
      if (file.size > 20 * 1024 * 1024) {
        alert(`Файл ${file.name} слишком большой (макс 20MB)`)
        continue
      }
      
      await compressAndSendImage(file)
    }
  } catch (error) {
    console.error('Ошибка отправки изображений:', error)
    alert('Не удалось отправить изображения: ' + error.message)
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

const compressAndSendImage = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      const img = new Image()
      
      img.onload = () => {
        try {
          const MAX_WIDTH = 1920
          const MAX_HEIGHT = 1080
          
          let width = img.width
          let height = img.height
          
          if (width > MAX_WIDTH || height > MAX_HEIGHT) {
            const ratio = Math.min(MAX_WIDTH / width, MAX_HEIGHT / height)
            width = Math.floor(width * ratio)
            height = Math.floor(height * ratio)
          }
          
          const canvas = document.createElement('canvas')
          canvas.width = width
          canvas.height = height
          
          const ctx = canvas.getContext('2d')
          ctx.drawImage(img, 0, 0, width, height)
          
          canvas.toBlob(async (blob) => {
            try {
              const formData = new FormData()
              formData.append('files', blob, file.name.replace(/\.[^/.]+$/, '.jpg'))
              
              const response = await axios.post('/api/chat/rooms/upload/', formData)
              
              if (response.data.status === 'success') {
                const uploadedFiles = response.data.data.files
                
                if (socket && socket.readyState === WebSocket.OPEN) {
                  socket.send(JSON.stringify({
                    type: 'message',
                    sender_id: auth.user.id,
                    text: '',
                    attachments: uploadedFiles.map(f => f.id)
                  }))
                }
              }
              
              resolve()
            } catch (error) {
              reject(error)
            }
          }, 'image/jpeg', 0.85)
        } catch (error) {
          reject(error)
        }
      }
      
      img.onerror = () => reject(new Error('Не удалось загрузить изображение'))
      img.src = e.target.result
    }
    
    reader.onerror = () => reject(new Error('Не удалось прочитать файл'))
    reader.readAsDataURL(file)
  })
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  
  if (files.length === 0) return
  
  for (const file of files) {
    if (file.size > 20 * 1024 * 1024) {
      alert(`Файл ${file.name} слишком большой (макс 20MB)`)
      continue
    }
    
    selectedFiles.value.push(file)
  }
  
  event.target.value = ''
}

const removeFile = (index) => { 
  selectedFiles.value.splice(index, 1) 
}

const uploadRawFiles = async () => {
  if (selectedFiles.value.length === 0) return []
  
  const formData = new FormData()
  
  selectedFiles.value.forEach(file => {
    formData.append('files', file)
  })
  
  try {
    const response = await axios.post('/api/chat/rooms/upload-raw-files/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success') {
      return response.data.data.files
    }
  } catch (error) {
    console.error('❌ [RAW] Ошибка загрузки:', error.response?.data)
    throw new Error(error.response?.data?.error || 'Ошибка загрузки файлов')
  }
  
  return []
}

const scrollToBottom = async (smooth = true) => {
  await nextTick()
  
  if (messagesContainer.value) {
    setTimeout(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTo({
          top: messagesContainer.value.scrollHeight,
          behavior: smooth ? 'smooth' : 'auto'
        })
      }
    }, 200)
  }
  
  if (mobileMessagesContainer.value) {
    setTimeout(() => {
      if (mobileMessagesContainer.value) {
        mobileMessagesContainer.value.scrollTo({
          top: mobileMessagesContainer.value.scrollHeight,
          behavior: smooth ? 'smooth' : 'auto'
        })
      }
    }, 200)
  }
}

const markAsRead = async () => {
  try {
    await axios.post(`/api/chat/rooms/${roomId}/mark-read/`)
    console.log('✅ Чат отмечен как прочитанный')
  } catch (error) {
    console.error('❌ Ошибка отметки прочитанного:', error)
  }
}

const fetchRoomDetails = async () => {
  try {
    const res = await axios.get(`/api/chat/rooms/${roomId}/`)
    const partnerId = res.data.data.members.find(id => String(id) !== String(auth.user.id))
    if (partnerId) {
      const userRes = await axios.post('/api/auth/users/batch/', { user_ids: [partnerId] })
      partner.value = { ...userRes.data.data[0], id: partnerId }
    }
  } catch (e) { console.error(e) }
}

const fetchHistory = async () => {
  try {
    const res = await axios.get(`/api/chat/rooms/${roomId}/messages/`)
    messages.value = res.data.data
    
    await nextTick()
    setTimeout(() => scrollToBottom(false), 250)
  } catch (e) { 
    console.error(e) 
  } finally { 
    loading.value = false 
  }
}

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsHost = import.meta.env.VITE_WS_HOST || 'localhost:8003'
  const token = auth.accessToken || localStorage.getItem('access_token')
  
  const wsUrl = `${wsProtocol}//${wsHost}/ws/chat/${roomId}/?token=${token}`
  
  console.log('🔌 Подключение к WebSocket:', wsUrl)
  
  socket = new WebSocket(wsUrl)
  
  socket.onopen = () => {
    console.log('✅ WebSocket подключен')
    isConnected.value = true
  }
  
  socket.onmessage = async (event) => {
    console.log('📨 Получено сообщение:', event.data)
    const data = JSON.parse(event.data)
    if (data.type === 'message') {
      const msg = data.data
      messages.value.push(msg)
      
      await nextTick()
      scrollToBottom(true)
      
      await markAsRead()
    } else if (data.type === 'message_updated') {
      const idx = messages.value.findIndex(m => String(m.id) === String(data.data.id))
      if (idx !== -1) messages.value[idx] = data.data
    }
  }
  
  socket.onerror = (error) => {
    console.error('❌ WebSocket ошибка:', error)
  }
  
  socket.onclose = (event) => {
    console.log('🔌 WebSocket закрыт:', event.code, event.reason)
    isConnected.value = false
    
    setTimeout(() => {
      if (!isConnected.value) {
        console.log('🔄 Попытка переподключения...')
        connectWebSocket()
      }
    }, 3000)
  }
}

const sendMessage = async () => {
  if ((!newMessage.value.trim() && selectedFiles.value.length === 0) || !isConnected.value || uploading.value) return
  
  try {
    uploading.value = true
    
    let uploadedFiles = []
    if (selectedFiles.value.length > 0) {
      uploadedFiles = await uploadRawFiles()
    }
    
    const messageData = { 
      type: 'message', 
      sender_id: auth.user.id, 
      text: newMessage.value.trim(),
      attachments: uploadedFiles.map(f => f.id)
    }
    
    console.log('📤 Отправка сообщения:', messageData)
    
    socket.send(JSON.stringify(messageData))
    
    newMessage.value = ''
    selectedFiles.value = []
    
    await nextTick()
    setTimeout(() => scrollToBottom(true), 200)
  } catch (error) {
    console.error('❌ Ошибка отправки:', error)
    alert('Ошибка отправки: ' + error.message)
  } finally {
    uploading.value = false
  }
}

const refreshMessages = () => fetchHistory()

watch(() => messages.value.length, async () => {
  if (messages.value.length > 0) {
    await nextTick()
    scrollToBottom(true)
  }
})

onMounted(async () => {
  await fetchRoomDetails()
  await fetchHistory()
  connectWebSocket()
  await markAsRead()
  
  setTimeout(() => scrollToBottom(false), 300)
})

onUnmounted(() => { 
  if (socket) {
    socket.close()
  }
})
</script>

<style scoped>
.glass { 
  background: rgba(255, 255, 255, 0.7); 
  backdrop-filter: blur(30px); 
}

@keyframes scale-in { 
  from { opacity: 0; transform: scale(0.98); } 
  to { opacity: 1; transform: scale(1); } 
}

.animate-scale-in { 
  animation: scale-in 0.15s ease forwards; 
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