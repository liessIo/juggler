// frontend/src/utils/axios.ts
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Session expired or invalid token
      const authStore = useAuthStore()
      authStore.logout()
      
      // Redirect to login
      router.push('/login')
      
      // Optional: Show message
      console.warn('Session expired. Please login again.')
    }
    return Promise.reject(error)
  }
)

export default api