<template>
  <div class="min-h-[80vh] flex items-center justify-center p-6">
    
    <div class="ios-glass-card w-full max-w-[400px] p-8 flex flex-col items-center animate-fade-in">
      
      <h1 class="text-3xl font-bold text-center mb-8 text-[#1a1a2e] drop-shadow-sm tracking-tight">
        С возвращением!
      </h1>

      <div class="w-full space-y-5">
        <div class="relative group">
          <input 
            v-model="email" 
            type="email" 
            placeholder="Почта" 
            class="ios-input"
          >
        </div>

        <div class="relative group">
          <input 
            v-model="password" 
            type="password" 
            placeholder="Пароль" 
            class="ios-input"
          >
        </div>
      </div>
      
      <button @click="handleLogin" class="ios-button mt-8">
        Войти
      </button>

      <p class="mt-6 text-center text-gray-500 text-sm font-medium">
        Нет аккаунта? 
        <router-link to="/register" class="text-[#7000ff] font-bold hover:opacity-70 transition-opacity">Зарегестрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const auth = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  const res = await auth.login(email.value, password.value)
  if (res.success) router.push('/')
  else alert('Login failed')
}
</script>

<style scoped>
/* ГЛАВНЫЙ ЭФФЕКТ: IOS THICK GLASS */
.ios-glass-card {
  /* Основа: Нейтральный серый полупрозрачный (как на часах), а не фиолетовый */
  background: rgba(255, 255, 255, 0.25);
  
  /* Размытие фона под карточкой */
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  
  /* Скругление */
  border-radius: 40px;
  
  /* ГРАНИ (BEVEL) - создают 3D объем стекла */
  border-top: 1px solid rgba(255, 255, 255, 0.8);
  border-left: 1px solid rgba(255, 255, 255, 0.4);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  
  /* Тени: Мягкая тень от карточки + внутренние блики */
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.1), 
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

/* ИНПУТЫ: Вдавленные в стекло */
.ios-input {
  width: 100%;
  padding: 16px 20px;
  /* Полупрозрачный фон, темнее самой карточки */
  background: rgba(0, 0, 0, 0.05); 
  border-radius: 20px;
  border: none;
  
  /* Внутренняя тень создает эффект углубления */
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
  box-shadow: 
    inset 0 1px 2px rgba(0, 0, 0, 0.05),
    0 0 0 2px rgba(112, 0, 255, 0.1); /* Легкий фиолетовый акцент при фокусе */
}

/* КНОПКА: Выпуклая линза */
.ios-button {
  width: 100%;
  padding: 16px;
  border-radius: 24px;
  font-weight: 700;
  font-size: 17px;
  color: white;
  
  /* Градиент или цвет кнопки */
  background: #7000ff; 
  
  /* Блики для объема */
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  
  box-shadow: 
    0 10px 20px rgba(112, 0, 255, 0.3),
    inset 0 2px 0 rgba(255, 255, 255, 0.2);
    
  transition: transform 0.1s;
}

.ios-button:active {
  transform: scale(0.96);
  filter: brightness(0.9);
}

.animate-fade-in {
  animation: fade-in 0.6s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>