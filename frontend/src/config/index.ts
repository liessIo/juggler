// frontend/src/config/index.ts
const config = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  API_BASE: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : 'http://localhost:8000/api',
  AUTH_TOKEN_KEY: 'juggler_access_token',
  REFRESH_TOKEN_KEY: 'juggler_refresh_token'
}

export default config