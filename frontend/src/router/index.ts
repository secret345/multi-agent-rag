import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginPage.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterPage.vue'),
    },
    {
      path: '/reset',
      name: 'reset',
      component: () => import('@/views/ResetPasswordPage.vue'),
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      redirect: '/chat',
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { name: 'chat' }
  }
})

export default router
