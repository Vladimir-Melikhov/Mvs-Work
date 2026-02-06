<template>
    <div class="glass p-6 md:p-8 rounded-[24px] md:rounded-[32px] space-y-6">
      <h3 class="text-lg md:text-xl font-bold text-[#1a1a2e] mb-6">Безопасность</h3>
      
      <!-- Смена Email -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-bold text-sm md:text-base text-[#1a1a2e]">Email</div>
            <div class="text-xs md:text-sm text-gray-500">{{ user?.email }}</div>
          </div>
          <button 
            @click="showEmailModal = true"
            class="text-xs md:text-sm font-bold text-[#7000ff] hover:underline"
          >
            Изменить
          </button>
        </div>
      </div>
  
      <div class="border-t border-white/20"></div>
  
      <!-- Смена пароля -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-bold text-sm md:text-base text-[#1a1a2e]">Пароль</div>
            <div class="text-xs md:text-sm text-gray-500">••••••••</div>
          </div>
          <button 
            @click="showPasswordModal = true"
            class="text-xs md:text-sm font-bold text-[#7000ff] hover:underline"
          >
            Изменить
          </button>
        </div>
      </div>
  
      <div class="border-t border-white/20"></div>
  
      <!-- Удаление аккаунта -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-bold text-sm md:text-base text-[#1a1a2e]">Удаление аккаунта</div>
            <div class="text-xs md:text-sm text-gray-500">Безвозвратное удаление всех данных</div>
          </div>
          <button 
            @click="showDeleteModal = true"
            class="text-xs md:text-sm font-bold text-red-500 hover:underline"
          >
            Удалить
          </button>
        </div>
      </div>
  
      <!-- Модальное окно смены Email -->
      <teleport to="body">
        <div v-if="showEmailModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div class="bg-white rounded-3xl p-6 md:p-8 max-w-md w-full shadow-2xl">
            <h3 class="text-xl font-bold mb-4 text-[#1a1a2e]">Изменить Email</h3>
            
            <p class="text-sm text-gray-600 mb-4">
              На новый email будет отправлен код подтверждения
            </p>
            
            <input 
              v-model="newEmail" 
              type="email" 
              placeholder="Новый email" 
              class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff] mb-4 text-sm"
            >
            
            <div v-if="emailError" class="mb-4 p-3 rounded-xl bg-red-50 text-red-500 text-xs font-bold">
              {{ emailError }}
            </div>
            
            <div v-if="emailSuccess" class="mb-4 p-3 rounded-xl bg-green-50 text-green-600 text-xs font-bold">
              {{ emailSuccess }}
            </div>
            
            <div class="flex gap-3">
              <button 
                @click="closeEmailModal"
                class="flex-1 border-2 border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-bold text-sm"
              >
                Отмена
              </button>
              <button 
                @click="updateEmail"
                :disabled="emailLoading || !newEmail"
                class="flex-1 bg-[#7000ff] text-white py-3 rounded-xl font-bold disabled:opacity-50 text-sm hover:bg-[#5500cc] transition-all"
              >
                {{ emailLoading ? 'Обновление...' : 'Обновить' }}
              </button>
            </div>
          </div>
        </div>
  
        <!-- Модальное окно смены пароля -->
        <div v-if="showPasswordModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div class="bg-white rounded-3xl p-6 md:p-8 max-w-md w-full shadow-2xl">
            <h3 class="text-xl font-bold mb-4 text-[#1a1a2e]">Изменить пароль</h3>
            
            <div class="space-y-4">
              <input 
                v-model="oldPassword" 
                type="password" 
                placeholder="Текущий пароль" 
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff] text-sm"
              >
              
              <input 
                v-model="newPassword" 
                type="password" 
                placeholder="Новый пароль (минимум 6 символов)" 
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff] text-sm"
              >
              
              <input 
                v-model="confirmNewPassword" 
                type="password" 
                placeholder="Повторите новый пароль" 
                class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff] text-sm"
                :class="{'border-red-400': newPassword && confirmNewPassword && newPassword !== confirmNewPassword}"
              >
            </div>
            
            <div v-if="passwordError" class="mt-4 p-3 rounded-xl bg-red-50 text-red-500 text-xs font-bold">
              {{ passwordError }}
            </div>
            
            <div v-if="passwordSuccess" class="mt-4 p-3 rounded-xl bg-green-50 text-green-600 text-xs font-bold">
              {{ passwordSuccess }}
            </div>
            
            <div class="flex gap-3 mt-6">
              <button 
                @click="closePasswordModal"
                class="flex-1 border-2 border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-bold text-sm"
              >
                Отмена
              </button>
              <button 
                @click="changePassword"
                :disabled="passwordLoading || !oldPassword || !newPassword || !confirmNewPassword"
                class="flex-1 bg-[#7000ff] text-white py-3 rounded-xl font-bold disabled:opacity-50 text-sm hover:bg-[#5500cc] transition-all"
              >
                {{ passwordLoading ? 'Обновление...' : 'Изменить' }}
              </button>
            </div>
          </div>
        </div>
  
        <!-- Модальное окно удаления аккаунта -->
        <div v-if="showDeleteModal" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div class="bg-white rounded-3xl p-6 md:p-8 max-w-md w-full shadow-2xl">
            <h3 class="text-xl font-bold mb-4 text-red-600">Удалить аккаунт?</h3>
            
            <p class="text-sm text-gray-600 mb-4">
              Это действие необратимо. Все ваши данные, услуги и сообщения будут удалены навсегда.
            </p>
            
            <input 
              v-model="deletePassword" 
              type="password" 
              placeholder="Введите ваш пароль для подтверждения" 
              class="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 mb-4 text-sm"
            >
            
            <div v-if="deleteError" class="mb-4 p-3 rounded-xl bg-red-50 text-red-500 text-xs font-bold">
              {{ deleteError }}
            </div>
            
            <div class="flex gap-3">
              <button 
                @click="closeDeleteModal"
                class="flex-1 border-2 border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-bold text-sm"
              >
                Отмена
              </button>
              <button 
                @click="deleteAccount"
                :disabled="deleteLoading || !deletePassword"
                class="flex-1 bg-red-600 text-white py-3 rounded-xl font-bold disabled:opacity-50 text-sm hover:bg-red-700 transition-all"
              >
                {{ deleteLoading ? 'Удаление...' : 'Удалить навсегда' }}
              </button>
            </div>
          </div>
        </div>
      </teleport>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  import { useAuthStore } from '../stores/authStore'
  import { useRouter } from 'vue-router'
  import axios from 'axios'
  
  const auth = useAuthStore()
  const router = useRouter()
  
  const user = computed(() => auth.user)
  
  // Email change
  const showEmailModal = ref(false)
  const newEmail = ref('')
  const emailError = ref('')
  const emailSuccess = ref('')
  const emailLoading = ref(false)
  
  // Password change
  const showPasswordModal = ref(false)
  const oldPassword = ref('')
  const newPassword = ref('')
  const confirmNewPassword = ref('')
  const passwordError = ref('')
  const passwordSuccess = ref('')
  const passwordLoading = ref(false)
  
  // Account deletion
  const showDeleteModal = ref(false)
  const deletePassword = ref('')
  const deleteError = ref('')
  const deleteLoading = ref(false)
  
  const closeEmailModal = () => {
    showEmailModal.value = false
    newEmail.value = ''
    emailError.value = ''
    emailSuccess.value = ''
  }
  
  const closePasswordModal = () => {
    showPasswordModal.value = false
    oldPassword.value = ''
    newPassword.value = ''
    confirmNewPassword.value = ''
    passwordError.value = ''
    passwordSuccess.value = ''
  }
  
  const closeDeleteModal = () => {
    showDeleteModal.value = false
    deletePassword.value = ''
    deleteError.value = ''
  }
  
  const updateEmail = async () => {
    if (!newEmail.value) {
      emailError.value = 'Введите новый email'
      return
    }
    
    emailError.value = ''
    emailSuccess.value = ''
    emailLoading.value = true
    
    try {
      const response = await axios.post('/api/auth/update-email/', {
        new_email: newEmail.value
      })
      
      if (response.data.status === 'success') {
        emailSuccess.value = 'Email обновлен! Проверьте новый email для подтверждения.'
        await auth.fetchProfile()
        
        setTimeout(() => {
          closeEmailModal()
        }, 2000)
      }
    } catch (error) {
      emailError.value = error.response?.data?.error || 'Ошибка обновления email'
    } finally {
      emailLoading.value = false
    }
  }
  
  const changePassword = async () => {
    if (newPassword.value.length < 6) {
      passwordError.value = 'Пароль должен быть не менее 6 символов'
      return
    }
    
    if (newPassword.value !== confirmNewPassword.value) {
      passwordError.value = 'Пароли не совпадают'
      return
    }
    
    passwordError.value = ''
    passwordSuccess.value = ''
    passwordLoading.value = true
    
    try {
      const response = await axios.post('/api/auth/change-password/', {
        old_password: oldPassword.value,
        new_password: newPassword.value
      })
      
      if (response.data.status === 'success') {
        passwordSuccess.value = 'Пароль успешно изменен!'
        
        setTimeout(() => {
          closePasswordModal()
        }, 2000)
      }
    } catch (error) {
      passwordError.value = error.response?.data?.error || 'Ошибка смены пароля'
    } finally {
      passwordLoading.value = false
    }
  }
  
  const deleteAccount = async () => {
    if (!deletePassword.value) {
      deleteError.value = 'Введите пароль для подтверждения'
      return
    }
    
    if (!confirm('Вы действительно хотите удалить аккаунт? Это действие нельзя отменить!')) {
      return
    }
    
    deleteError.value = ''
    deleteLoading.value = true
    
    try {
      const response = await axios.delete('/api/auth/delete-account/', {
        data: { password: deletePassword.value }
      })
      
      if (response.data.status === 'success') {
        alert('Аккаунт успешно удален')
        auth.logout()
        router.push('/login')
      }
    } catch (error) {
      deleteError.value = error.response?.data?.error || 'Ошибка удаления аккаунта'
    } finally {
      deleteLoading.value = false
    }
  }
  </script>
  
  <style scoped>
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.07);
  }
  </style>