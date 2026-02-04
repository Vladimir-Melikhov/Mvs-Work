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
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)

  // КРИТИЧНО: Пропускаем публичные страницы БЕЗ проверки токена
  if (!requiresAuth && !requiresGuest) {
    return next()
  }

  // Проверяем токен ТОЛЬКО на страницах с requiresGuest или requiresAuth
  if (!auth.isInitialized) {
    // Для страниц login/register НЕ вызываем initAuth (не проверяем токен)
    if (requiresGuest) {
      auth.isInitialized = true
      return next()
    }
    
    // Для защищенных страниц - проверяем токен
    await auth.initAuth()
  }

  const isAuthenticated = auth.isAuthenticated

  // Если не авторизован и страница требует авторизацию
  if (!isAuthenticated && requiresAuth) {
    return next('/login')
  }

  // Если авторизован и пытается зайти на login/register
  if (isAuthenticated && requiresGuest) {
    return next('/')
  }

  // Проверка email verification
  if (isAuthenticated && auth.user && !auth.user.email_verified) {
    if (to.name !== 'verify-email') {
      return next('/verify-email')
    }
    return next()
  }

  // Редирект с verify-email если email уже подтвержден
  if (isAuthenticated && auth.user && auth.user.email_verified && to.name === 'verify-email') {
    return next('/')
  }

  // Проверка заполненности профиля для worker
  if (isAuthenticated && auth.user && auth.user.email_verified) {
    const isWorker = auth.user.role === 'worker'
    const isProfileIncomplete = isWorker && (!auth.user.profile?.skills || auth.user.profile.skills.length === 0)
    
    if (isProfileIncomplete && to.name !== 'onboarding') {
      return next('/onboarding')
    }
    
    if (!isProfileIncomplete && to.name === 'onboarding') {
      return next('/')
    }
  }

  next()
})

export default router