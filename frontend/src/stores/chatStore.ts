/**
 * File: src/stores/chatStore.ts
 * Pinia Store for Juggler Multi-Provider Chat Application
 * Manages global application state, provider switching, and conversations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { JugglerAPI, type ChatRequest } from '@/services/api'
import type {
  ChatMessage,
  Conversation,
  AIProvider,
  AIModel,
  ChatState,
  ProviderSwitchOptions,
} from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // State
  const conversations = ref<Conversation[]>([])
  const activeConversationId = ref<string | null>(null)
  const providers = ref<AIProvider[]>([])
  const currentProvider = ref<string>('ollama')
  const currentModel = ref<string>('')
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('disconnected')

  // Computed
  const activeConversation = computed(() => {
    if (!activeConversationId.value) return null
    return conversations.value.find(conv => conv.id === activeConversationId.value) || null
  })

  const availableProviders = computed(() => {
    return providers.value.filter(provider => provider.status === 'healthy')
  })

  const currentProviderData = computed(() => {
    return providers.value.find(p => p.id === currentProvider.value)
  })

  const availableModels = computed(() => {
    const provider = currentProviderData.value
    return provider ? provider.models : []
  })

  const hasHealthyProviders = computed(() => {
    return providers.value.some(p => p.status === 'healthy')
  })

  // Actions
  async function initialize() {
    console.log('Initializing chat store...')
    await testConnection()
    await loadProviders()
    createNewConversation()
  }

  async function testConnection() {
    connectionStatus.value = 'connecting'
    try {
      const isConnected = await JugglerAPI.testConnection()
      connectionStatus.value = isConnected ? 'connected' : 'disconnected'
      
      if (!isConnected) {
        error.value = 'Cannot connect to backend. Make sure the FastAPI server is running on port 8000.'
      } else {
        error.value = null
      }
      
      return isConnected
    } catch (err) {
      connectionStatus.value = 'disconnected'
      error.value = 'Backend connection failed'
      return false
    }
  }

  async function loadProviders() {
    try {
      isLoading.value = true
      const response = await JugglerAPI.getProviders()
      
      providers.value = response.providers.map(provider => ({
        id: provider.id,
        name: provider.name,
        status: provider.status as 'healthy' | 'degraded' | 'down' | 'not_configured',
        models: provider.models.map(model => ({
          id: model.id,
          name: model.name,
          provider: model.provider,
          contextWindow: model.context_window || 4096,
          supportsVision: model.supports_vision,
        })),
        latencyMs: provider.latency_ms,
      }))

      // Set default provider to first healthy one
      const healthyProvider = providers.value.find(p => p.status === 'healthy')
      if (healthyProvider) {
        currentProvider.value = healthyProvider.id
        if (healthyProvider.models.length > 0) {
          currentModel.value = healthyProvider.models[0].id
        }
      }

      console.log(`Loaded ${response.providers.length} providers, ${response.healthy_providers} healthy`)
    } catch (err: any) {
      error.value = `Failed to load providers: ${err.message}`
      console.error('Provider loading error:', err)
    } finally {
      isLoading.value = false
    }
  }

  function createNewConversation(title?: string) {
    const conversation: Conversation = {
      id: Date.now().toString(),
      title: title || `Chat ${conversations.value.length + 1}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      currentProvider: currentProvider.value,
      currentModel: currentModel.value,
      totalTokens: 0,
    }

    conversations.value.push(conversation)
    activeConversationId.value = conversation.id
    return conversation
  }

  function setActiveConversation(conversationId: string) {
    const conversation = conversations.value.find(conv => conv.id === conversationId)
    if (conversation) {
      activeConversationId.value = conversationId
      currentProvider.value = conversation.currentProvider
      currentModel.value = conversation.currentModel
    }
  }

  async function sendMessage(content: string) {
    if (!activeConversation.value) {
      createNewConversation()
    }

    const conversation = activeConversation.value
    if (!conversation) return

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      role: 'user',
      provider: currentProvider.value,
      model: currentModel.value,
      timestamp: new Date(),
    }

    conversation.messages.push(userMessage)
    conversation.updatedAt = new Date()

    // Update conversation title if first message
    if (conversation.messages.length === 1) {
      conversation.title = content.length > 30 ? content.substring(0, 30) + '...' : content
    }

    isLoading.value = true
    error.value = null

    try {
      // Build conversation history for context
      const conversationHistory = conversation.messages
        .filter(msg => msg.role !== 'system') // Exclude system messages
        .map(msg => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content
        }))

      const request: ChatRequest = {
        message: content,
        provider: currentProvider.value,
        model: currentModel.value,
        conversation_history: conversationHistory
      }

      const response = await JugglerAPI.sendMessage(request)

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        role: 'assistant',
        provider: response.provider,
        model: response.model,
        timestamp: new Date(),
        latency_ms: response.latency_ms,
        tokens: response.input_tokens && response.output_tokens ? {
          input: response.input_tokens,
          output: response.output_tokens,
        } : undefined,
      }

      conversation.messages.push(assistantMessage)
      conversation.updatedAt = new Date()

      // Update token count
      if (assistantMessage.tokens) {
        conversation.totalTokens += assistantMessage.tokens.input + assistantMessage.tokens.output
      }

    } catch (err: any) {
      error.value = `Chat error: ${err.message}`
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${err.message}`,
        role: 'assistant',
        provider: currentProvider.value,
        model: currentModel.value,
        timestamp: new Date(),
        error: err.message,
      }
      conversation.messages.push(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  async function switchProvider(options: ProviderSwitchOptions) {
    const targetProvider = providers.value.find(p => p.id === options.targetProvider)
    if (!targetProvider || targetProvider.status !== 'healthy') {
      error.value = `Provider ${options.targetProvider} is not available`
      return false
    }

    const targetModel = options.targetModel || targetProvider.models[0]?.id
    if (!targetModel) {
      error.value = `No models available for provider ${options.targetProvider}`
      return false
    }

    const previousProvider = currentProvider.value
    const previousModel = currentModel.value

    // Update current provider/model
    currentProvider.value = options.targetProvider
    currentModel.value = targetModel

    // Update active conversation
    if (activeConversation.value) {
      activeConversation.value.currentProvider = options.targetProvider
      activeConversation.value.currentModel = targetModel
      activeConversation.value.updatedAt = new Date()

      // Add system message about switch
      if (options.preserveContext) {
        const switchMessage: ChatMessage = {
          id: Date.now().toString(),
          content: `Switched from ${previousProvider}/${previousModel} to ${options.targetProvider}/${targetModel} with context preservation`,
          role: 'system',
          provider: options.targetProvider,
          model: targetModel,
          timestamp: new Date(),
        }
        activeConversation.value.messages.push(switchMessage)
      }
    }

    console.log(`Switched provider: ${previousProvider} → ${options.targetProvider}`)
    return true
  }

  function clearError() {
    error.value = null
  }

  function deleteConversation(conversationId: string) {
    const index = conversations.value.findIndex(conv => conv.id === conversationId)
    if (index !== -1) {
      conversations.value.splice(index, 1)
      
      // If deleted conversation was active, switch to most recent
      if (activeConversationId.value === conversationId) {
        if (conversations.value.length > 0) {
          activeConversationId.value = conversations.value[conversations.value.length - 1].id
        } else {
          activeConversationId.value = null
          createNewConversation()
        }
      }
    }
  }

  function exportConversation(conversationId: string) {
    const conversation = conversations.value.find(conv => conv.id === conversationId)
    if (!conversation) return null

    const exportData = {
      title: conversation.title,
      createdAt: conversation.createdAt,
      totalTokens: conversation.totalTokens,
      messages: conversation.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        provider: msg.provider,
        model: msg.model,
        timestamp: msg.timestamp,
        latency_ms: msg.latency_ms,
        tokens: msg.tokens,
      })),
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = `juggler-chat-${conversation.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`
    a.click()
    
    URL.revokeObjectURL(url)
  }

  // Return store interface
  return {
    // State
    conversations,
    activeConversationId,
    providers,
    currentProvider,
    currentModel,
    isLoading,
    error,
    connectionStatus,

    // Computed
    activeConversation,
    availableProviders,
    currentProviderData,
    availableModels,
    hasHealthyProviders,

    // Actions
    initialize,
    testConnection,
    loadProviders,
    createNewConversation,
    setActiveConversation,
    sendMessage,
    switchProvider,
    clearError,
    deleteConversation,
    exportConversation,
  }
})