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
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'

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
      component: ServiceDetailView,
      meta: { requiresEmailVerification: false }
    },
    {
      path: '/create-service',
      name: 'create-service',
      component: CreateServiceView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
    },
    {
      path: '/my-services/edit/:id',
      name: 'edit-service',
      component: CreateServiceView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
    },
    {
      path: '/chats',
      name: 'chats',
      component: ChatsView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
    },
    {
      path: '/chats/:id', 
      name: 'chat-detail',
      component: ChatDetailView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
    },
    {
      path: '/users/:id',
      name: 'public-profile',
      component: PublicProfileView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
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
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: { requiresGuest: true }
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPasswordView,
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
      meta: { requiresAuth: true, requiresEmailVerification: true }
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
  const requiresEmailVerification = to.matched.some(record => record.meta.requiresEmailVerification)

  // Публичные страницы - пропускаем без проверки
  if (!requiresAuth && !requiresGuest) {
    return next()
  }

  // Проверяем токен только на защищенных страницах
  if (!auth.isInitialized) {
    if (requiresGuest) {
      auth.isInitialized = true
      return next()
    }
    
    await auth.initAuth()
  }

  const isAuthenticated = auth.isAuthenticated

  // Редирект неавторизованных с защищенных страниц
  if (!isAuthenticated && requiresAuth) {
    return next('/login')
  }

  // Редирект авторизованных с гостевых страниц
  if (isAuthenticated && requiresGuest) {
    return next('/')
  }

  // Проверка подтверждения email
  if (isAuthenticated && auth.user) {
    const emailVerified = auth.user.email_verified
    
    // Если email не подтвержден и страница требует подтверждения
    if (!emailVerified && requiresEmailVerification) {
      if (to.name !== 'verify-email') {
        return next('/verify-email')
      }
    }
    
    // Если email подтвержден и пользователь на странице верификации
    if (emailVerified && to.name === 'verify-email') {
      return next('/')
    }
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
