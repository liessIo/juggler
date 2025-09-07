// stores/chatStore.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import config from '@/config'
import type { 
  ChatSession, 
  Message, 
  Provider, 
  ProviderStatus,
  RefreshResponse,
  RefreshAllResponse 
} from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // State
  const sessions = ref<Map<string, ChatSession>>(new Map())
  const currentSessionId = ref<string | null>(null)
  const providers = ref<Record<string, ProviderStatus>>({})
  const currentProvider = ref<string>('')
  const currentModel = ref<string>('')
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(false)

  // Computed
  const currentSession = computed(() => {
    if (!currentSessionId.value) return null
    return sessions.value.get(currentSessionId.value) || null
  })

  const availableProviders = computed(() => {
    console.log('Computing available providers from:', providers.value)
    return Object.entries(providers.value)
      .filter(([_, provider]) => provider.available && provider.models && provider.models.length > 0)
      .map(([name, provider]) => ({
        name,
        available: provider.available,
        models: provider.models
      }))
  })

  // Helper function to get auth headers
  function getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    
    const token = localStorage.getItem(config.AUTH_TOKEN_KEY)
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  // Error handling
  function setError(message: string) {
    error.value = message
    console.error('Chat store error:', message)
  }

  function clearError() {
    error.value = null
  }

  // Provider management
  async function fetchProviders(): Promise<void> {
    try {
      console.log('Fetching providers...')
      
      // For status endpoint, we don't need auth (it should be public)
      const response = await fetch(`${config.API_BASE}/providers/status`)

      if (!response.ok) {
        throw new Error(`Failed to fetch providers: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('Providers data received:', data)
      
      providers.value = data

      // Set default provider and model if none selected
      if (!currentProvider.value && availableProviders.value.length > 0) {
        const firstProvider = availableProviders.value[0]
        currentProvider.value = firstProvider.name
        
        if (firstProvider.models.length > 0) {
          currentModel.value = firstProvider.models[0]
        }
      }
    } catch (err: any) {
      console.error('Error fetching providers:', err)
      setError(`Failed to load providers: ${err.message}`)
      providers.value = {}
    }
  }

  async function refreshProviderModels(providerName: string): Promise<RefreshResponse> {
    try {
      console.log(`Refreshing models for ${providerName}...`)
      
      const response = await fetch(`${config.API_BASE}/providers/${providerName}/refresh`, {
        method: 'POST',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to refresh ${providerName} models`)
      }

      const data = await response.json()
      console.log(`Refresh response for ${providerName}:`, data)

      // Update the provider in our store
      if (providers.value[providerName]) {
        providers.value[providerName].models = data.models
      }

      return {
        success: true,
        provider: providerName,
        models: data.models,
        count: data.count,
        refreshed_at: data.refreshed_at
      }
    } catch (err: any) {
      console.error(`Error refreshing ${providerName} models:`, err)
      throw new Error(err.message)
    }
  }

  async function refreshAllProviders(): Promise<RefreshAllResponse> {
    try {
      console.log('Refreshing all providers...')
      
      const response = await fetch(`${config.API_BASE}/providers/refresh-all`, {
        method: 'POST',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to refresh all providers')
      }

      const data = await response.json()
      console.log('Refresh all response:', data)

      // Update all providers in our store
      Object.entries(data.providers).forEach(([providerName, providerData]: [string, any]) => {
        if (providers.value[providerName] && providerData.success) {
          providers.value[providerName].models = providerData.models
        }
      })

      return {
        success: true,
        providers: data.providers,
        refreshed_at: data.refreshed_at
      }
    } catch (err: any) {
      console.error('Error refreshing all providers:', err)
      throw new Error(err.message)
    }
  }

  function switchProvider(providerId: string): void {
    console.log(`Switching to provider: ${providerId}`)
    
    if (!providers.value[providerId]?.available) {
      setError(`Provider ${providerId} is not available`)
      return
    }

    currentProvider.value = providerId
    
    // Reset model to first available model for new provider
    const providerModels = providers.value[providerId]?.models || []
    if (providerModels.length > 0) {
      currentModel.value = providerModels[0]
      console.log(`Switched to model: ${currentModel.value}`)
    } else {
      currentModel.value = ''
      console.warn(`No models available for provider: ${providerId}`)
    }

    clearError()
  }

  // Message handling
  async function sendMessage(content: string): Promise<void> {
    if (!content.trim()) return
    if (!currentProvider.value || !currentModel.value) {
      setError('Please select a provider and model')
      return
    }

    isLoading.value = true
    clearError()

    try {
      // Create user message
      const userMessage: Message = {
        id: generateMessageId(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
        provider: currentProvider.value,
        model: currentModel.value
      }

      // Add to current session or create new one
      let sessionId = currentSessionId.value
      if (!sessionId) {
        sessionId = await createNewSession()
      }

      const session = sessions.value.get(sessionId)
      if (session) {
        session.messages.push(userMessage)
        session.updatedAt = new Date()
      }

      // Send to API
      const response = await fetch(`${config.API_BASE}/chat/send`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          content: content.trim(),
          provider: currentProvider.value,
          model: currentModel.value,
          conversation_id: sessionId
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to send message')
      }

      const data = await response.json()
      
      // Create assistant message
      const assistantMessage: Message = {
        id: generateMessageId(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        provider: currentProvider.value,
        model: currentModel.value
      }

      // Add assistant response to session
      if (session) {
        session.messages.push(assistantMessage)
        session.updatedAt = new Date()
      }

      console.log('Message sent successfully')
    } catch (err: any) {
      console.error('Error sending message:', err)
      setError(err.message)
    } finally {
      isLoading.value = false
    }
  }

  async function createNewSession(): Promise<string> {
    const sessionId = generateSessionId()
    const newSession: ChatSession = {
      id: sessionId,
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    }

    sessions.value.set(sessionId, newSession)
    currentSessionId.value = sessionId
    console.log('Created new session:', sessionId)
    
    return sessionId
  }

  function generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  function generateMessageId(): string {
    return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  // Conversation management
  async function loadConversations(): Promise<void> {
    try {
      const response = await fetch(`${config.API_BASE}/chat/conversations`, {
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('Failed to load conversations')
      }

      const data = await response.json()
      
      // Convert to sessions map
      sessions.value.clear()
      data.conversations.forEach((conv: any) => {
        const session: ChatSession = {
          id: conv.id,
          title: conv.title,
          messages: [], // Will be loaded when conversation is opened
          createdAt: new Date(conv.created_at),
          updatedAt: new Date(conv.updated_at)
        }
        sessions.value.set(conv.id, session)
      })

      console.log(`Loaded ${data.conversations.length} conversations`)
    } catch (err: any) {
      console.error('Error loading conversations:', err)
      setError('Failed to load conversations')
    }
  }

  async function loadConversation(conversationId: string): Promise<void> {
    try {
      const response = await fetch(`${config.API_BASE}/chat/conversation/${conversationId}`, {
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('Failed to load conversation')
      }

      const data = await response.json()
      
      // Convert messages
      const messages: Message[] = data.messages.map((msg: any) => ({
        id: generateMessageId(),
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at),
        provider: msg.provider,
        model: msg.model
      }))

      // Update session
      const session = sessions.value.get(conversationId)
      if (session) {
        session.messages = messages
        currentSessionId.value = conversationId
      }

      console.log(`Loaded conversation ${conversationId} with ${messages.length} messages`)
    } catch (err: any) {
      console.error('Error loading conversation:', err)
      setError('Failed to load conversation')
    }
  }

  // Initialization
  async function initialize(): Promise<void> {
    console.log('Initializing chat store...')
    
    try {
      // Always fetch providers first (status endpoint is public)
      await fetchProviders()
      
      // Check if user is authenticated by checking token existence
      const token = localStorage.getItem(config.AUTH_TOKEN_KEY)
      if (token) {
        console.log('User authenticated, loading conversations...')
        await loadConversations()
      } else {
        console.log('User not authenticated, skipping conversation loading')
      }
      
      isInitialized.value = true
      console.log('Chat store initialized successfully')
      
    } catch (err: any) {
      console.error('Error during initialization:', err)
      setError(`Initialization failed: ${err.message}`)
    }
  }

  // Reset store state
  function reset(): void {
    sessions.value.clear()
    currentSessionId.value = null
    providers.value = {}
    currentProvider.value = ''
    currentModel.value = ''
    isLoading.value = false
    error.value = null
    isInitialized.value = false
  }

  return {
    // State
    sessions,
    currentSessionId,
    providers,
    currentProvider,
    currentModel,
    isLoading,
    error,
    isInitialized,

    // Computed
    currentSession,
    availableProviders,

    // Actions
    setError,
    clearError,
    fetchProviders,
    refreshProviderModels,
    refreshAllProviders,
    switchProvider,
    sendMessage,
    createNewSession,
    loadConversations,
    loadConversation,
    initialize,
    reset
  }
})