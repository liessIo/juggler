<template>
  <div class="chat-interface">
    <!-- Header with Provider Selection -->
    <div class="chat-header">
      <div class="provider-info">
        <h2>Juggler Multi-Provider Chat</h2>
        <div class="connection-status" :class="connectionStatusClass">
          {{ connectionStatusText }}
        </div>
      </div>
      
      <!-- Provider and Model Selector -->
      <div v-if="availableProviders && availableProviders.length > 0" class="provider-selector-wrapper">
        <div class="selector-group">
          <label>Provider:</label>
          <select v-model="currentProvider" @change="handleProviderChange(currentProvider)">
            <option v-for="provider in availableProviders" :key="provider.name" :value="provider.name">
              {{ provider.name }}
            </option>
          </select>
        </div>
        
        <div class="selector-group" v-if="currentProviderModels.length > 0">
          <label>Model:</label>
          <div class="model-selector-container">
            <select v-model="currentModel" @change="handleModelChange(currentModel)">
              <option v-for="model in currentProviderModels" :key="model" :value="model">
                {{ formatModelName(model) }}
              </option>
            </select>
            
            <!-- Refresh Button -->
            <button 
              @click="refreshCurrentProviderModels" 
              :disabled="isRefreshingModels"
              class="refresh-button"
              :title="`Refresh ${currentProvider} models`"
            >
              <svg 
                :class="{ 'spinning': isRefreshingModels }" 
                width="16" 
                height="16" 
                viewBox="0 0 24 24" 
                fill="currentColor"
              >
                <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z"/>
              </svg>
            </button>
            
            <!-- Refresh All Button -->
            <button 
              @click="refreshAllProviders" 
              :disabled="isRefreshingAll"
              class="refresh-all-button"
              title="Refresh all provider models"
            >
              <svg 
                :class="{ 'spinning': isRefreshingAll }" 
                width="16" 
                height="16" 
                viewBox="0 0 24 24" 
                fill="currentColor"
              >
                <path d="M12,18A6,6 0 0,1 6,12C6,11 6.25,10.03 6.7,9.2L5.24,7.74C4.46,8.97 4,10.43 4,12A8,8 0 0,0 12,20V23L16,19L12,15M12,4V1L8,5L12,9V6A6,6 0 0,1 18,12C18,13 17.75,13.97 17.3,14.8L18.76,16.26C19.54,15.03 20,13.57 20,12A8,8 0 0,0 12,4Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="no-providers">
        <span>No providers available</span>
        <button @click="refreshAllProviders" class="retry-button">
          Retry Connection
        </button>
      </div>
    </div>

    <!-- Success/Info Banner -->
    <div v-if="successMessage" class="success-banner">
      <span>{{ successMessage }}</span>
      <button @click="clearSuccessMessage" class="banner-close">&times;</button>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="error-banner">
      <span>{{ error }}</span>
      <button @click="clearError" class="banner-close">&times;</button>
    </div>

    <!-- Chat Messages Area -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="!currentSession || !currentSession.messages || currentSession.messages.length === 0" class="welcome-message">
        <h3>Welcome to Juggler</h3>
        <p>Start a conversation with any AI provider. You can switch providers mid-conversation while preserving context.</p>
        
        <!-- Show available providers if any -->
        <div v-if="availableProviders && availableProviders.length > 0" class="provider-stats">
          <div v-for="provider in availableProviders" :key="provider.name" class="provider-stat">
            <div class="provider-name">{{ provider.name }}</div>
            <div class="provider-models">{{ provider.models.length }} models</div>
            <div class="provider-status" :class="`status-${provider.available ? 'online' : 'offline'}`">
              {{ provider.available ? 'Online' : 'Offline' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Messages List -->
      <div v-if="currentSession && currentSession.messages" class="messages-list">
        <div v-for="message in currentSession.messages" :key="message.id" class="message-bubble" :class="`message-${message.role}`">
          <div class="message-content">{{ message.content }}</div>
          <div class="message-meta">
            {{ message.role }} • {{ formatTime(message.timestamp) }}
            <span v-if="message.provider"> • {{ message.provider }}</span>
            <span v-if="message.model"> • {{ formatModelName(message.model) }}</span>
          </div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="isLoading" class="loading-indicator">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span>{{ currentProvider }} is thinking...</span>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <div class="input-container">
        <textarea
          v-model="inputMessage"
          @keydown="handleKeyDown"
          placeholder="Type your message... (Shift+Enter for new line, Enter to send)"
          class="message-input"
          :disabled="isLoading || !hasHealthyProviders"
          rows="1"
          ref="textareaRef"
        ></textarea>
        
        <button
          @click="sendMessage"
          class="send-button"
          :disabled="!canSend"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
      
      <div class="input-footer">
        <div class="current-model">
          <span v-if="currentProvider && currentModel">
            {{ currentProvider }} • {{ formatModelName(currentModel) }}
          </span>
        </div>
        
        <div class="conversation-stats" v-if="currentSession">
          <span>{{ currentSession.messages?.length || 0 }} messages</span>
          <span v-if="lastRefresh" class="last-refresh">
            Models updated: {{ formatTime(lastRefresh) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chatStore'

console.log('ChatInterface component loading...')

const chatStore = useChatStore()
console.log('ChatStore loaded:', chatStore)

// Store reactive references
const {
  currentSession,
  availableProviders,
  currentProvider,
  currentModel,
  isLoading,
  error,
  providers,
  isInitialized,
} = storeToRefs(chatStore)

console.log('Store refs created')

// Local reactive state
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const textareaRef = ref<HTMLTextAreaElement>()
const isRefreshingModels = ref(false)
const isRefreshingAll = ref(false)
const successMessage = ref('')
const lastRefresh = ref<Date | null>(null)

// Computed properties
const hasHealthyProviders = computed(() => {
  return availableProviders.value && availableProviders.value.length > 0
})

const currentProviderModels = computed(() => {
  if (!providers.value || !currentProvider.value) return []
  const provider = providers.value[currentProvider.value as keyof typeof providers.value]
  return provider?.models || []
})

const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 && 
         !isLoading.value && 
         hasHealthyProviders.value &&
         !isRefreshingModels.value &&
         !isRefreshingAll.value
})

const connectionStatus = computed(() => {
  if (!providers.value) return 'disconnected'
  if (isLoading.value || isRefreshingAll.value) return 'connecting'
  return hasHealthyProviders.value ? 'connected' : 'disconnected'
})

const connectionStatusClass = computed(() => {
  return `status-${connectionStatus.value}`
})

const connectionStatusText = computed(() => {
  if (isRefreshingAll.value) return 'Refreshing...'
  switch (connectionStatus.value) {
    case 'connected':
      return 'Connected'
    case 'connecting':
      return 'Connecting...'
    case 'disconnected':
      return 'Disconnected'
    default:
      return 'Unknown'
  }
})

// Methods
async function sendMessage() {
  console.log('Sending message:', inputMessage.value)
  if (!canSend.value) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  // Auto-resize textarea back to single line
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }

  await chatStore.sendMessage(message)
  await scrollToBottom()
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function handleProviderChange(providerId: string) {
  console.log('Switching provider to:', providerId)
  chatStore.switchProvider(providerId)
  
  // Set first available model for new provider
  const models = currentProviderModels.value
  if (models.length > 0 && !models.includes(currentModel.value)) {
    currentModel.value = models[0]
    chatStore.currentModel = models[0]
  }
}

function handleModelChange(modelId: string) {
  console.log('Switching model to:', modelId)
  chatStore.currentModel = modelId
}

async function refreshCurrentProviderModels() {
  if (!currentProvider.value || isRefreshingModels.value) return
  
  isRefreshingModels.value = true
  clearSuccessMessage()
  
  try {
    console.log(`Refreshing models for ${currentProvider.value}...`)
    
    // Call the new refresh endpoint
    const response = await chatStore.refreshProviderModels(currentProvider.value)
    
    if (response.success) {
      successMessage.value = `Refreshed ${response.count} models for ${currentProvider.value}`
      lastRefresh.value = new Date()
      
      // Auto-clear success message after 3 seconds
      setTimeout(() => {
        clearSuccessMessage()
      }, 3000)
      
      console.log(`Successfully refreshed ${response.count} models for ${currentProvider.value}`)
      
      // Update current model if it's no longer available
      const models = currentProviderModels.value
      if (models.length > 0 && !models.includes(currentModel.value)) {
        currentModel.value = models[0]
        chatStore.currentModel = models[0]
      }
    }
  } catch (error: any) {
    console.error('Failed to refresh provider models:', error)
    chatStore.setError(`Failed to refresh ${currentProvider.value} models: ${error.message}`)
  } finally {
    isRefreshingModels.value = false
  }
}

async function refreshAllProviders() {
  if (isRefreshingAll.value) return
  
  isRefreshingAll.value = true
  clearSuccessMessage()
  
  try {
    console.log('Refreshing all providers...')
    
    // Call the refresh-all endpoint
    const response = await chatStore.refreshAllProviders()
    
    if (response.success) {
      const totalModels = Object.values(response.providers)
        .reduce((sum: number, provider: any) => sum + (provider.count || 0), 0)
      
      successMessage.value = `Refreshed ${totalModels} models across all providers`
      lastRefresh.value = new Date()
      
      // Auto-clear success message after 4 seconds
      setTimeout(() => {
        clearSuccessMessage()
      }, 4000)
      
      console.log('Successfully refreshed all providers')
      
      // Re-initialize the store to pick up new providers/models
      await chatStore.initialize()
    }
  } catch (error: any) {
    console.error('Failed to refresh all providers:', error)
    chatStore.setError(`Failed to refresh providers: ${error.message}`)
  } finally {
    isRefreshingAll.value = false
  }
}

function formatModelName(model: string): string {
  // Make model names more readable
  const modelNames: Record<string, string> = {
    'llama3:8b': 'Llama 3 (8B)',
    'llama3:8b-gpu': 'Llama 3 GPU (8B)',
    'llama-3.1-70b-versatile': 'Llama 3.1 (70B)',
    'llama-3.1-8b-instant': 'Llama 3.1 Instant (8B)',
    'mixtral-8x7b-32768': 'Mixtral (8x7B)',
    'nomic-embed-text:latest': 'Nomic Embed Text',
    'gemini-pro': 'Gemini Pro',
    'gemini-pro-vision': 'Gemini Pro Vision',
    'gemma2-9b-it': 'Gemma 2 (9B)',
    'llama3.2:latest': 'Llama 3.2',
    'llama3.2:1b': 'Llama 3.2 (1B)',
    'llama3.2:3b': 'Llama 3.2 (3B)'
  }
  return modelNames[model] || model
}

function clearError() {
  chatStore.clearError()
}

function clearSuccessMessage() {
  successMessage.value = ''
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function formatTime(timestamp: Date | string): string {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
  return date.toLocaleTimeString()
}

// Auto-resize textarea
function autoResizeTextarea() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px'
  }
}

// Watchers
watch(inputMessage, () => {
  autoResizeTextarea()
})

watch(() => currentSession.value?.messages?.length, () => {
  scrollToBottom()
})

// Auto-refresh models on provider change
watch(currentProvider, async (newProvider, oldProvider) => {
  if (newProvider && newProvider !== oldProvider && isInitialized.value) {
    console.log(`Provider changed to ${newProvider}, checking if refresh needed...`)
    
    // Check if models are cached and recent
    const models = currentProviderModels.value
    if (models.length === 0) {
      console.log(`No models found for ${newProvider}, auto-refreshing...`)
      await refreshCurrentProviderModels()
    }
  }
})

// Lifecycle
onMounted(async () => {
  console.log('ChatInterface mounted, initializing store...')
  try {
    await chatStore.initialize()
    console.log('Store initialized successfully')
    console.log('Providers:', providers.value)
    console.log('Available:', availableProviders.value)
    
    // Set initial refresh time
    lastRefresh.value = new Date()
  } catch (err) {
    console.error('Failed to initialize:', err)
  }
  await scrollToBottom()
})
</script>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.provider-info h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  color: #333;
}

.connection-status {
  font-size: 0.875rem;
  font-weight: 500;
}

.status-connected {
  color: #059669;
}

.status-connecting {
  color: #d97706;
}

.status-disconnected {
  color: #dc2626;
}

.provider-selector-wrapper {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.selector-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.selector-group select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  min-width: 120px;
}

.model-selector-container {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.refresh-button, .refresh-all-button {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #6b7280;
}

.refresh-button:hover:not(:disabled), 
.refresh-all-button:hover:not(:disabled) {
  background: #f9fafb;
  color: #374151;
  border-color: #9ca3af;
}

.refresh-button:disabled, 
.refresh-all-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-all-button {
  background: #eff6ff;
  border-color: #dbeafe;
  color: #2563eb;
}

.refresh-all-button:hover:not(:disabled) {
  background: #dbeafe;
  border-color: #93c5fd;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.no-providers {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #9ca3af;
  font-style: italic;
}

.retry-button {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.retry-button:hover {
  background: #2563eb;
}

.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: #f0fdf4;
  border-left: 4px solid #22c55e;
  color: #166534;
}

.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: #fef2f2;
  border-left: 4px solid #dc2626;
  color: #991b1b;
}

.banner-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  margin-left: 1rem;
  opacity: 0.7;
}

.banner-close:hover {
  opacity: 1;
}

.success-banner .banner-close {
  color: #166534;
}

.error-banner .banner-close {
  color: #991b1b;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  scroll-behavior: smooth;
}

.welcome-message {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.welcome-message h3 {
  color: #374151;
  margin-bottom: 1rem;
}

.provider-stats {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.provider-stat {
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  min-width: 120px;
}

.provider-name {
  font-weight: 600;
  color: #374151;
}

.provider-models {
  font-size: 0.875rem;
  color: #6b7280;
}

.provider-status {
  font-size: 0.75rem;
  margin-top: 0.25rem;
  font-weight: 500;
}

.status-online {
  color: #059669;
}

.status-offline {
  color: #dc2626;
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
}

.message-bubble {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  max-width: 70%;
}

.message-user {
  background: #3b82f6;
  color: white;
  margin-left: auto;
  text-align: right;
}

.message-assistant {
  background: white;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.message-content {
  margin-bottom: 0.25rem;
  white-space: pre-wrap;
}

.message-meta {
  font-size: 0.75rem;
  opacity: 0.7;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  color: #6b7280;
  max-width: 800px;
  margin: 0 auto;
}

.loading-dots {
  display: flex;
  gap: 0.25rem;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #9ca3af;
  animation: pulse 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes pulse {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  background: white;
  border-top: 1px solid #e0e0e0;
  padding: 1rem;
}

.input-container {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  max-width: 800px;
  margin: 0 auto;
}

.message-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  line-height: 1.5;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  font-family: inherit;
}

.message-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-input:disabled {
  background-color: #f9fafb;
  color: #9ca3af;
}

.send-button {
  padding: 0.75rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  height: 44px;
  transition: background-color 0.2s;
}

.send-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.send-button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  margin-top: 0.5rem;
}

.current-model {
  font-weight: 500;
}

.conversation-stats {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.last-refresh {
  font-size: 0.75rem;
  opacity: 0.8;
  font-style: italic;
}
</style>