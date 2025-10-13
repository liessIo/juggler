import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../components/LoginForm.vue')
    },
    {
      path: '/',
      name: 'Chat',
      component: () => import('../ChatView.vue'),
      meta: { 
        requiresAuth: true,
        keepAlive: true  // NEW
      }
    },
    {
      path: '/config',
      name: 'Config',
      component: () => import('../components/ConfigView.vue'),
      meta: { 
        requiresAuth: true,
        keepAlive: false  // Config immer fresh
      }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router