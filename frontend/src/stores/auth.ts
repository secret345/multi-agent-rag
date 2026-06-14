import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const phone = ref(localStorage.getItem('phone') || '')

  const isAuthenticated = computed(() => !!token.value)

  async function login(phoneNum: string, password: string) {
    const { data } = await client.post('/auth/login', { phone: phoneNum, password })
    token.value = data.access_token
    phone.value = phoneNum
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('phone', phoneNum)
  }

  async function register(phoneNum: string, password: string) {
    await client.post('/auth/register', { phone: phoneNum, password })
  }

  function logout() {
    token.value = ''
    phone.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('phone')
  }

  return { token, phone, isAuthenticated, login, register, logout }
})
