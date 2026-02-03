import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import SearchView from '../views/SearchView.vue'
import ChatsView from '../views/ChatsView.vue'
import ProfileView from '../views/ProfileView.vue'
import PublicProfileView from '../views/PublicProfileView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import OnboardingView from '../views/OnboardingView.vue'
import ServiceDetailView from '../views/ServiceDetailView.vue'
import CreateServiceView from '../views/CreateServiceView.vue'
import ChatDetailView from '../views/ChatDetailView.vue'
import VerifyEmailView from '../views/VerifyEmailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/search'
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/services/:id',
      name: 'service-detail',
      component: ServiceDetailView
    },
    {
      path: '/create-service',
      name: 'create-service',
      component: CreateServiceView,
      meta: { requiresAuth: true }
    },
    {
      path: '/my-services/edit/:id',
      name: 'edit-service',
      component: CreateServiceView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chats',
      name: 'chats',
      component: ChatsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chats/:id', 
      name: 'chat-detail',
      component: ChatDetailView,
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/users/:id',
      name: 'public-profile',
      component: PublicProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresGuest: true }
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: VerifyEmailView,
      meta: { requiresAuth: true }
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: OnboardingView,
      meta: { requiresAuth: true }
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth'
      }
    }
    
    return { top: 0 }
  }
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  
  // Ждем инициализации auth (попытка refresh токена)
  if (!auth.isInitialized) {
    await auth.initAuth()
  }

  const isAuthenticated = auth.isAuthenticated
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)

  // ===== ПОЛЬЗОВАТЕЛЬ НЕ АВТОРИЗОВАН =====
  if (!isAuthenticated) {
    // Пытается зайти на защищенную страницу → редирект на логин
    if (requiresAuth) {
      return next('/login')
    }
    // Разрешаем доступ к гостевым страницам
    return next()
  }

  // ===== ПОЛЬЗОВАТЕЛЬ АВТОРИЗОВАН =====

  // Проверка верификации email (ТОЛЬКО для авторизованных!)
  if (auth.user && !auth.user.email_verified) {
    // Если не подтвержден email и пытается зайти НЕ на verify-email
    if (to.name !== 'verify-email') {
      return next('/verify-email')
    }
    // Уже на странице верификации - пускаем
    return next()
  }

  // Если email подтвержден, но пытается зайти на страницу верификации
  if (auth.user && auth.user.email_verified && to.name === 'verify-email') {
    return next('/')
  }

  // Проверка заполненности профиля для воркеров
  if (auth.user && auth.user.email_verified) {
    const isWorker = auth.user.role === 'worker'
    const isProfileIncomplete = isWorker && (!auth.user.profile.skills || auth.user.profile.skills.length === 0)
    
    if (isProfileIncomplete && to.name !== 'onboarding') {
      return next('/onboarding')
    }
    
    if (!isProfileIncomplete && to.name === 'onboarding') {
      return next('/')
    }
  }

  // Если уже залогинен и пытается зайти на login/register
  if (requiresGuest) {
    return next('/')
  }

  // Все проверки пройдены - разрешаем переход
  next()
})

export default router
