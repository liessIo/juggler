/**
 * File: src/services/api.ts
 * API Service for Juggler Multi-Provider Chat
 * Handles communication with FastAPI backend
 */

import axios from 'axios'

// Backend API base URL
const API_BASE_URL = 'http://localhost:8000'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for chat responses
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API Service class
export class JugglerAPI {
  /**
   * Check if backend is healthy
   */
  static async healthCheck(): Promise<any> {
    try {
      const response = await apiClient.get('/health')
      return response.data
    } catch (error) {
      throw new Error('Backend health check failed')
    }
  }

  /**
   * Get available providers and their models
   */
  static async getProviders(): Promise<ProvidersResponse> {
    try {
      const response = await apiClient.get('/providers')
      return response.data
    } catch (error) {
      console.error('Failed to fetch providers:', error)
      throw new Error('Could not load AI providers')
    }
  }

  /**
   * Send chat message to specified provider
   */
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await apiClient.post('/chat', request)
      return response.data
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Chat request failed'
      throw new Error(errorMessage)
    }
  }

  /**
   * Switch provider while preserving context
   */
  static async switchProvider(
    currentProvider: string,
    targetProvider: string,
    message: string
  ): Promise<any> {
    try {
      const response = await apiClient.post('/chat/switch', null, {
        params: {
          current_provider: currentProvider,
          target_provider: targetProvider,
          message: message,
        },
      })
      return response.data
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Provider switch failed'
      throw new Error(errorMessage)
    }
  }

  /**
   * Test connection to backend
   */
  static async testConnection(): Promise<boolean> {
    try {
      const response = await apiClient.get('/')
      return response.status === 200
    } catch (error) {
      return false
    }
  }
}

// Type definitions to match FastAPI backend
export interface ChatRequest {
  message: string
  provider: string
  model?: string
  temperature?: number
  max_tokens?: number
  conversation_history?: Array<{
    role: 'user' | 'assistant' | 'system'
    content: string
  }>
}

export interface ChatResponse {
  response: string
  provider: string
  model: string
  latency_ms: number
  input_tokens?: number
  output_tokens?: number
}

export interface ModelInfo {
  id: string
  name: string
  provider: string
  context_window?: number
  supports_vision: boolean
}

export interface ProviderInfo {
  id: string
  name: string
  status: string
  models: ModelInfo[]
  latency_ms?: number
}

export interface ProvidersResponse {
  providers: ProviderInfo[]
  total_models: number
  healthy_providers: number
}

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  provider: string
  model: string
  timestamp: Date
  latency_ms?: number
  token_count?: {
    input: number
    output: number
  }
}

// Utility functions
export const formatLatency = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export const formatTokenCount = (inputTokens?: number, outputTokens?: number): string => {
  if (!inputTokens || !outputTokens) return 'N/A'
  return `${inputTokens + outputTokens} tokens`
}

export const getProviderColor = (provider: string): string => {
  switch (provider) {
    case 'ollama':
      return '#10B981' // Green
    case 'groq':
      return '#8B5CF6' // Purple
    case 'gemini':
      return '#3B82F6' // Blue
    case 'openai':
      return '#EF4444' // Red
    default:
      return '#6B7280' // Gray
  }
}

export default JugglerAPI