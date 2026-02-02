// frontend/src/components/PrivacyPolicyModal.vue
<template>
  <teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/50 z-[9999] flex items-center justify-center p-4" @click.self="$emit('close')">
      <div class="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-2xl font-bold text-[#1a1a2e]">Политика конфиденциальности</h2>
          <button @click="$emit('close')" class="w-10 h-10 rounded-full hover:bg-gray-100 flex items-center justify-center">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="overflow-y-auto px-6 py-6 max-h-[calc(90vh-80px)]">
          <div class="prose prose-sm max-w-none">
            <h3>1. Общие положения</h3>
            <p>Настоящая Политика конфиденциальности определяет порядок обработки и защиты персональных данных пользователей сервиса Mvs-Work в соответствии с Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных».</p>
            
            <h3>2. Обрабатываемые данные</h3>
            <p>Мы обрабатываем следующие категории персональных данных:</p>
            <ul>
              <li>Email адрес</li>
              <li>ФИО (при указании в профиле)</li>
              <li>Фотография профиля (аватар)</li>
              <li>Информация о навыках и опыте работы</li>
              <li>История переписки и сделок</li>
              <li>Telegram ID (при подключении уведомлений)</li>
            </ul>
            
            <h3>3. Цели обработки данных</h3>
            <p>Персональные данные обрабатываются в следующих целях:</p>
            <ul>
              <li>Предоставление доступа к функционалу платформы</li>
              <li>Идентификация пользователя</li>
              <li>Обработка платежей и финансовых операций</li>
              <li>Отправка уведомлений о событиях на платформе</li>
              <li>Разрешение споров между пользователями</li>
            </ul>
            
            <h3>4. Правовые основания обработки</h3>
            <p>Обработка персональных данных осуществляется на основании:</p>
            <ul>
              <li>Согласия субъекта персональных данных (ст. 9 ФЗ-152)</li>
              <li>Исполнения договора (ст. 6 ФЗ-152)</li>
            </ul>
            
            <h3>5. Сроки хранения данных</h3>
            <p>Персональные данные хранятся в течение:</p>
            <ul>
              <li>Срока действия учетной записи пользователя</li>
              <li>3 года после удаления аккаунта (для разрешения споров)</li>
              <li>Финансовые данные - 5 лет (в соответствии с НК РФ)</li>
            </ul>
            
            <h3>6. Права субъекта персональных данных</h3>
            <p>Вы имеете право:</p>
            <ul>
              <li>Получать информацию о наличии и содержании ваших данных</li>
              <li>Требовать уточнения или удаления данных</li>
              <li>Отозвать согласие на обработку данных</li>
              <li>Обжаловать действия оператора в Роскомнадзоре или суде</li>
            </ul>
            
            <h3>7. Меры защиты данных</h3>
            <p>Мы применяем следующие меры защиты:</p>
            <ul>
              <li>Шифрование передачи данных (HTTPS/WSS)</li>
              <li>Хеширование паролей</li>
              <li>Ограничение доступа к персональным данным</li>
              <li>Регулярное резервное копирование</li>
              <li>Мониторинг безопасности</li>
            </ul>
            
            <h3>8. Передача данных третьим лицам</h3>
            <p>Персональные данные не передаются третьим лицам, за исключением:</p>
            <ul>
              <li>Случаев, предусмотренных законодательством РФ</li>
              <li>С вашего явного согласия</li>
            </ul>
            
            <h3>9. Контактная информация</h3>
            <p>По вопросам обработки персональных данных:</p>
            <p>Email: privacy@mvs-work.ru</p>
            
            <h3>10. Изменения политики</h3>
            <p>Мы оставляем за собой право вносить изменения в настоящую Политику. Актуальная версия всегда доступна на сайте.</p>
            
            <p class="text-sm text-gray-500 mt-6">Дата последнего обновления: 02.02.2026</p>
          </div>
        </div>
        
        <div class="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4">
          <button 
            @click="$emit('accept')" 
            class="w-full bg-[#7000ff] hover:bg-[#5500cc] text-white py-3 rounded-xl font-bold transition-all"
          >
            Я ознакомлен и согласен
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
defineProps({
  show: Boolean
})

defineEmits(['close', 'accept'])
</script>