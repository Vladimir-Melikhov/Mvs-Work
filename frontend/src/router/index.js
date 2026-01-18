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
    // ✅ НОВЫЙ МАРШРУТ: Публичный профиль пользователя
    {
      path: '/users/:id',
      name: 'public-profile',
      component: PublicProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: OnboardingView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if (token && !auth.user) {
    try {
      await auth.fetchProfile()
    } catch (e) {
      return next('/login')
    }
  }

  if (auth.user) {
    const isWorker = auth.user.role === 'worker'
    const isProfileIncomplete = isWorker && (!auth.user.profile.skills || auth.user.profile.skills.length === 0)
    
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
