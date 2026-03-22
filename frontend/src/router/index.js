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
import Error404View from '../views/Error404View.vue'
import Error500View from '../views/Error500View.vue'
import Error403View from '../views/Error403View.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/search'
    },
    // ── Публичные страницы (без авторизации) ──────────────────────────────────
    {
      path: '/search',
      name: 'search',
      component: SearchView,
      meta: { requiresAuth: false, requiresGuest: false, requiresEmailVerification: false }
    },
    {
      path: '/services/:id',
      name: 'service-detail',
      component: ServiceDetailView,
      meta: { requiresAuth: false, requiresGuest: false, requiresEmailVerification: false }
    },
    {
      path: '/users/:id',
      name: 'public-profile',
      component: PublicProfileView,
      meta: { requiresAuth: false, requiresGuest: false, requiresEmailVerification: false }
    },
    // ── Страницы только для гостей ────────────────────────────────────────────
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
    // ── Защищённые страницы (нужна авторизация) ───────────────────────────────
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
      path: '/verify-email',
      name: 'verify-email',
      component: VerifyEmailView,
      meta: { requiresAuth: true, requiresEmailVerification: false }
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: OnboardingView,
      meta: { requiresAuth: true, requiresEmailVerification: true }
    },
    // ── Страницы ошибок ───────────────────────────────────────────────────────
    {
      path: '/403',
      name: 'error-403',
      component: Error403View,
      meta: { requiresAuth: false, requiresGuest: false, requiresEmailVerification: false }
    },
    {
      path: '/500',
      name: 'error-500',
      component: Error500View,
      meta: { requiresAuth: false, requiresGuest: false, requiresEmailVerification: false }
    },
    // ── Catch-all 404 ─────────────────────────────────────────────────────────
    {
      path: '/:pathMatch(.*)*',
      name: 'error-404',
      component: Error404View,
      meta: { requiresAuth: false, requiresGuest: false, requiresEmailVerification: false }
    },
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0 }
  }
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  const requiresAuth = to.meta.requiresAuth === true
  const requiresGuest = to.meta.requiresGuest === true
  const requiresEmailVerification = to.meta.requiresEmailVerification === true

  // ── 1. Полностью публичные страницы — пропускаем без любых проверок ─────────
  if (!requiresAuth && !requiresGuest) {
    return next()
  }

  // ── 2. Инициализируем auth если нужно ────────────────────────────────────────
  if (!auth.isInitialized) {
    if (requiresGuest) {
      auth.isInitialized = true
    } else {
      await auth.initAuth()
    }
  }

  const isAuthenticated = auth.isAuthenticated

  // ── 3. Защищённые страницы — редирект неавторизованных на /login ─────────────
  if (requiresAuth && !isAuthenticated) {
    return next('/login')
  }

  // ── 4. Гостевые страницы — редирект авторизованных на главную ────────────────
  if (requiresGuest && isAuthenticated) {
    return next('/')
  }

  // ── 5. Проверка подтверждения email ──────────────────────────────────────────
  if (isAuthenticated && auth.user) {
    const emailVerified = auth.user.email_verified

    if (!emailVerified && requiresEmailVerification) {
      if (to.name !== 'verify-email') {
        return next('/verify-email')
      }
    }

    if (emailVerified && to.name === 'verify-email') {
      return next('/')
    }
  }

  // ── 6. Проверка заполненности профиля воркера ─────────────────────────────────
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
