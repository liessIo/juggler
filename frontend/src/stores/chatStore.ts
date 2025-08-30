/**
 * File: src/types/chat.ts
 * TypeScript type definitions for Juggler Chat Application
 */

// Core chat message structure
export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant' | 'system'
  provider: string
  model: string
  timestamp: Date
  latency_ms?: number
  tokens?: {
    input: number
    output: number
  }
  error?: string
}

// Conversation management
export interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: Date
  updatedAt: Date
  currentProvider: string
  currentModel: string
  totalTokens: number
}

// Provider and model definitions
export interface AIModel {
  id: string
  name: string
  provider: string
  contextWindow: number
  supportsVision: boolean
  costPer1MTokens?: number
}

export interface AIProvider {
  id: string
  name: string
  status: 'healthy' | 'degraded' | 'down' | 'not_configured'
  models: AIModel[]
  latencyMs?: number
  description?: string
  features?: string[]
}

// API request/response types
export interface SendMessageRequest {
  message: string
  provider: string
  model?: string
  temperature?: number
  maxTokens?: number
  conversationId?: string
  conversation_history?: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

export interface SendMessageResponse {
  response: string
  provider: string
  model: string
  latencyMs: number
  inputTokens?: number
  outputTokens?: number
}

// UI state management
export interface ChatState {
  conversations: Conversation[]
  activeConversationId: string | null
  providers: AIProvider[]
  isLoading: boolean
  error: string | null
  connectionStatus: 'connected' | 'connecting' | 'disconnected'
}

export interface UISettings {
  theme: 'light' | 'dark'
  showTokenCounts: boolean
  showLatency: boolean
  autoScroll: boolean
  compactMode: boolean
  preferredProvider: string
  preferredModel: string
}

// Context transfer types
export interface ContextTransferRequest {
  fromProvider: string
  toProvider: string
  conversationId: string
  preserveMessages: number // How many recent messages to include
  includeSystemPrompt: boolean
}

export interface ContextTransferResponse {
  success: boolean
  transferredMessages: number
  summary?: string
  error?: string
}

// Provider switching types
export interface ProviderSwitchOptions {
  targetProvider: string
  targetModel?: string
  preserveContext: boolean
  contextSummary?: boolean
}

// Statistics and analytics
export interface ConversationStats {
  totalMessages: number
  totalTokens: number
  averageLatency: number
  providerUsage: Record<string, number>
  modelUsage: Record<string, number>
  totalCost?: number
}

export interface ProviderStats {
  providerId: string
  totalRequests: number
  totalTokens: number
  averageLatency: number
  errorRate: number
  uptime: number
  lastHealthCheck: Date
}

// Error handling
export interface APIError {
  code: string
  message: string
  details?: any
  timestamp: Date
}

export interface ChatError extends APIError {
  provider: string
  model?: string
  conversationId?: string
  retryable: boolean
}

// Utility types
export type MessageRole = 'user' | 'assistant' | 'system'
export type ProviderStatus = 'healthy' | 'degraded' | 'down' | 'not_configured'
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected'

// Component prop types
export interface MessageBubbleProps {
  message: ChatMessage
  showMetadata?: boolean
  compact?: boolean
}

export interface ProviderSelectorProps {
  providers: AIProvider[]
  selectedProvider: string
  selectedModel?: string
  onProviderChange: (provider: string, model?: string) => void
  disabled?: boolean
}

export interface ChatInterfaceProps {
  conversation?: Conversation
  onSendMessage: (message: string) => void
  onProviderSwitch: (options: ProviderSwitchOptions) => void
  isLoading?: boolean
}

// Event types
export interface MessageSentEvent {
  message: string
  provider: string
  model: string
  conversationId: string
}

export interface MessageReceivedEvent {
  response: ChatMessage
  conversationId: string
}

export interface ProviderSwitchedEvent {
  fromProvider: string
  toProvider: string
  fromModel?: string
  toModel?: string
  conversationId: string
  contextTransferred: boolean
}

export interface ErrorEvent {
  error: ChatError
  context?: any
}

// Constants
export const MESSAGE_ROLES = {
  USER: 'user' as MessageRole,
  ASSISTANT: 'assistant' as MessageRole,
  SYSTEM: 'system' as MessageRole,
} as const

export const PROVIDER_STATUS = {
  HEALTHY: 'healthy' as ProviderStatus,
  DEGRADED: 'degraded' as ProviderStatus,
  DOWN: 'down' as ProviderStatus,
  NOT_CONFIGURED: 'not_configured' as ProviderStatus,
} as const

export const CONNECTION_STATUS = {
  CONNECTED: 'connected' as ConnectionStatus,
  CONNECTING: 'connecting' as ConnectionStatus,
  DISCONNECTED: 'disconnected' as ConnectionStatus,
} as const

// Helper functions
export const createMessage = (
  content: string,
  role: MessageRole,
  provider: string,
  model: string
): ChatMessage => ({
  id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
  content,
  role,
  provider,
  model,
  timestamp: new Date(),
})

export const createConversation = (
  title: string,
  provider: string,
  model: string
): Conversation => ({
  id: Date.now().toString(),
  title,
  messages: [],
  createdAt: new Date(),
  updatedAt: new Date(),
  currentProvider: provider,
  currentModel: model,
  totalTokens: 0,
})

export const formatTimestamp = (date: Date): string => {
  return date.toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

export const getProviderDisplayName = (providerId: string): string => {
  const displayNames: Record<string, string> = {
    'ollama': 'Ollama (Local)',
    'groq': 'Groq',
    'gemini': 'Google Gemini',
    'openai': 'OpenAI',
  }
  return displayNames[providerId] || providerId
}