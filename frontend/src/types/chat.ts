// types/chat.ts

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  provider?: string
  model?: string
  metadata?: Record<string, any>
}

export interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  metadata?: Record<string, any>
}

export interface ProviderStatus {
  available: boolean
  models: string[]
  lastRefresh?: Date
  error?: string
}

export interface Provider {
  name: string
  available: boolean
  models: string[]
  lastRefresh?: Date
  error?: string
}

export interface RefreshResponse {
  success: boolean
  provider: string
  models: string[]
  count: number
  refreshed_at: string
  error?: string
}

export interface RefreshAllResponse {
  success: boolean
  providers: Record<string, {
    success: boolean
    models: string[]
    count?: number
    error?: string
  }>
  refreshed_at: string
}

export interface SendMessageRequest {
  content: string
  provider: string
  model?: string
  conversation_id?: string
}

export interface SendMessageResponse {
  response: string
  conversation_id: string
  provider: string
  model?: string
  timestamp: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserCredentials {
  username: string
  password: string
}

export interface UserRegistration extends UserCredentials {
  email: string
}

export interface ConversationSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export interface ConversationsResponse {
  conversations: ConversationSummary[]
  total: number
}

export interface ConversationDetail {
  id: string
  title: string
  messages: Array<{
    role: string
    content: string
    provider?: string
    model?: string
    created_at: string
  }>
  created_at: string
}

export interface ApiError {
  detail: string
  status_code?: number
}

export interface HealthCheck {
  status: string
  timestamp: string
  version: string
}

// Provider-specific model information
export interface ModelInfo {
  id: string
  name: string
  description?: string
  context_length?: number
  capabilities?: string[]
}

// Enhanced provider status with model details
export interface EnhancedProviderStatus extends ProviderStatus {
  models_info?: ModelInfo[]
  last_error?: string
  response_time?: number
  rate_limit?: {
    requests_per_minute: number
    current_usage: number
  }
}

// Chat store state interface
export interface ChatStoreState {
  sessions: Map<string, ChatSession>
  currentSessionId: string | null
  providers: Record<string, ProviderStatus>
  currentProvider: string
  currentModel: string
  isLoading: boolean
  error: string | null
  isInitialized: boolean
  authToken: string | null
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'message' | 'status' | 'error' | 'ping' | 'pong'
  data: any
  timestamp: string
}

export interface StreamingMessage {
  id: string
  delta: string
  finished: boolean
  metadata?: Record<string, any>
}

// Configuration types
export interface AppConfig {
  apiBase: string
  wsBase: string
  maxMessageLength: number
  maxConversations: number
  autoSave: boolean
  theme: 'light' | 'dark' | 'auto'
}

// Export utility types
export type ProviderName = 'ollama' | 'groq' | 'gemini' | 'openai' | 'anthropic'
export type MessageRole = Message['role']
export type ChatStoreAction = 
  | 'initialize'
  | 'sendMessage' 
  | 'switchProvider'
  | 'refreshModels'
  | 'loadConversation'
  | 'createSession'
  | 'deleteSession'