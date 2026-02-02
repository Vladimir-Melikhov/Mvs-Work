// frontend/src/views/RegisterView.vue
<template>
  <div class="min-h-[85vh] flex items-center justify-center p-6 pt-16">
    <div class="ios-glass-card w-full max-w-[420px] p-8 flex flex-col items-center animate-fade-in">
      
      <h1 class="text-3xl font-bold text-center mb-2 text-[#1a1a2e] tracking-tight">Добро пожаловать!</h1>
      <p class="text-center text-gray-500 mb-8 text-sm font-medium">Присоеденитесь к нам уже сейчас!</p>
      
      <div class="role-selector w-full p-1.5 rounded-[22px] mb-8 flex relative">
        <div 
          class="absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] bg-white/90 rounded-[18px] shadow-sm transition-all duration-300 ease-out"
          :class="role === 'client' ? 'left-1.5' : 'left-[calc(50%+3px)]'"
        ></div>
        <button 
          @click="role = 'client'" 
          class="role-btn"
          :class="role === 'client' ? 'text-[#1a1a2e]' : 'text-gray-500'"
        >
          Я заказчик
        </button>
        <button 
          @click="role = 'worker'" 
          class="role-btn"
          :class="role === 'worker' ? 'text-[#7000ff]' : 'text-gray-500'"
        >
          Я исполнитель
        </button>
      </div>

      <div class="w-full space-y-4">
        <input 
          v-model="email" 
          type="email" 
          placeholder="Почта" 
          class="ios-input"
        >
        
        <input 
          v-model="password" 
          type="password" 
          placeholder="Пароль (минимум 6 символов)" 
          class="ios-input"
        >

        <input 
          v-model="confirmPassword" 
          type="password" 
          placeholder="Повторите пароль" 
          class="ios-input"
          :class="{'border-red-400 bg-red-50/50': password && confirmPassword && password !== confirmPassword}"
        >
      </div>

      <div class="w-full mt-4">
        <label class="flex items-start gap-3 cursor-pointer">
          <input 
            type="checkbox" 
            v-model="agreedToPolicy" 
            class="mt-1 w-5 h-5 rounded border-gray-300 text-[#7000ff] focus:ring-[#7000ff]"
          >
          <span class="text-sm text-gray-600">
            Я согласен с 
            <button @click.prevent="showPrivacyPolicy = true" class="text-[#7000ff] font-semibold hover:underline">
              политикой конфиденциальности
            </button>
            и даю согласие на обработку персональных данных
          </span>
        </label>
      </div>

      <div v-if="errorMessage" class="mt-4 p-3 rounded-2xl bg-red-50/80 text-red-500 text-xs font-bold text-center border border-red-100 w-full animate-fade-in">
        {{ errorMessage }}
      </div>
      
      <button 
        @click="handleRegister" 
        :disabled="isLoading || !agreedToPolicy"
        class="ios-button mt-8"
      >
        {{ isLoading ? 'Создаем аккаунт...' : 'Создать аккаунт' }}
      </button>

      <p class="mt-6 text-center text-gray-500 text-sm font-medium">
        Есть аккаунт?
        <router-link to="/login" class="text-[#7000ff] font-bold hover:opacity-70 transition-opacity">Войти</router-link>
      </p>
    </div>
    
    <PrivacyPolicyModal 
      :show="showPrivacyPolicy" 
      @close="showPrivacyPolicy = false"
      @accept="handlePolicyAccept"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'
import PrivacyPolicyModal from '../components/PrivacyPolicyModal.vue'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const role = ref('client')
const errorMessage = ref('')
const isLoading = ref(false)
const agreedToPolicy = ref(false)
const showPrivacyPolicy = ref(false)

const auth = useAuthStore()
const router = useRouter()

const handlePolicyAccept = () => {
  agreedToPolicy.value = true
  showPrivacyPolicy.value = false
}

const handleRegister = async () => {
  if (!agreedToPolicy.value) {
    errorMessage.value = "Необходимо согласие на обработку персональных данных"
    return
  }

  if (!email.value || password.value.length < 6) {
    errorMessage.value = "Введите корректный email и пароль (минимум 6 символов)"
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Пароли не совпадают!"
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  const res = await auth.register(email.value, password.value, role.value)
  
  if (res.success) {
    router.push('/onboarding')
  } else {
    const err = res.error
    errorMessage.value = typeof err === 'object' ? Object.values(err).flat().join(', ') : err
  }
  
  isLoading.value = false
}
</script>

<style scoped>
.ios-glass-card {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-radius: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.8);
  border-left: 1px solid rgba(255, 255, 255, 0.4);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.1), 
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

.role-selector {
  background: rgba(0, 0, 0, 0.05);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.role-btn {
  flex: 1;
  padding: 12px 0;
  font-size: 14px;
  font-weight: 700;
  position: relative;
  z-index: 10;
  transition: color 0.3s ease;
}

.ios-input {
  width: 100%;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.05); 
  border-radius: 20px;
  border: 1px solid transparent;
  box-shadow: 
    inset 0 2px 4px rgba(0, 0, 0, 0.05), 
    0 1px 0 rgba(255, 255, 255, 0.5);
  color: #1a1a2e;
  font-size: 16px;
  outline: none;
  transition: all 0.3s ease;
}

.ios-input::placeholder {
  color: rgba(0, 0, 0, 0.4);
}

.ios-input:focus {
  background: rgba(255, 255, 255, 0.5);
  border-color: rgba(112, 0, 255, 0.1);
  box-shadow: 
    inset 0 1px 2px rgba(0, 0, 0, 0.05),
    0 0 0 4px rgba(112, 0, 255, 0.05);
}

.ios-button {
  width: 100%;
  padding: 18px;
  border-radius: 24px;
  font-weight: 700;
  font-size: 17px;
  color: white;
  background: #7000ff; 
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 
    0 12px 24px rgba(112, 0, 255, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.2);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.ios-button:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.ios-button:active:not(:disabled) {
  transform: scale(0.97);
  filter: brightness(0.9);
}

.ios-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #a8a8a8;
  box-shadow: none;
}

.animate-fade-in {
  animation: fade-in 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes fade-in {
  from { opacity: 0; transform: scale(0.96) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
