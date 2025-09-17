// frontend/src/stores/auth.ts
import { defineStore } from 'pinia'
import axios from 'axios'
import { ref, computed } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface User {
  id: string
  username: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!token.value)

  // Set axios default header if token exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  async function login(username: string, password: string) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username,
        password
      })
      
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      
      // Store tokens
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      
      // Set axios header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
      
      // Fetch user info
      await fetchUser()
      
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' }
    }
  }

  async function register(username: string, email: string, password: string) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
        username,
        email,
        password
      })
      
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      
      // Store tokens
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      
      // Set axios header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
      
      // Fetch user info
      await fetchUser()
      
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' }
    }
  }

  async function fetchUser() {
    if (!token.value) return
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/me`)
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    refreshToken.value = null
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    
    delete axios.defaults.headers.common['Authorization']
  }

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser
  }
})