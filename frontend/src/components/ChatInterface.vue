<template>
  <!-- 
    File: src/components/ChatInterface.vue
    Main chat interface component for Juggler
    Handles message display, input, and provider switching
  -->


  <div class="chat-interface">
    <!-- Header with Provider Selection -->
    <div class="chat-header">
      <div class="provider-info">
        <h2>Juggler Multi-Provider Chat</h2>
        <div class="connection-status" :class="connectionStatusClass">
          {{ connectionStatusText }}
        </div>
      </div>
      
      <ProviderSelector
        :providers="availableProviders"
        :selectedProvider="currentProvider"
        :selectedModel="currentModel"
        @providerChange="handleProviderChange"
        :disabled="isLoading"
      />
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="error-banner">
      <span>{{ error }}</span>
      <button @click="clearError" class="error-close">&times;</button>
    </div>

    <!-- Chat Messages Area -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="!activeConversation || activeConversation.messages.length === 0" class="welcome-message">
        <h3>Welcome to Juggler</h3>
        <p>Start a conversation with any AI provider. You can switch providers mid-conversation while preserving context.</p>
        <div class="provider-stats">
          <div v-for="provider in availableProviders" :key="provider.id" class="provider-stat">
            <div class="provider-name">{{ provider.name }}</div>
            <div class="provider-models">{{ provider.models.length }} models</div>
            <div v-if="provider.latencyMs" class="provider-latency">{{ provider.latencyMs }}ms</div>
          </div>
        </div>
      </div>

      <div v-if="activeConversation" class="messages-list">
        <MessageBubble
          v-for="message in activeConversation.messages"
          :key="message.id"
          :message="message"
          :showMetadata="true"
        />
      </div>

      <!-- Loading indicator -->
      <div v-if="isLoading" class="loading-indicator">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span>{{ currentProviderData?.name || currentProvider }} is thinking...</span>
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
          <span v-if="currentProviderData">
            {{ currentProviderData.name }} • {{ currentModel }}
          </span>
        </div>
        
        <div class="conversation-stats" v-if="activeConversation">
          <span>{{ activeConversation.messages.length }} messages</span>
          <span v-if="activeConversation.totalTokens > 0">
            • {{ activeConversation.totalTokens }} tokens
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
import MessageBubble from './MessageBubble.vue'
import ProviderSelector from './ProviderSelector.vue'

const chatStore = useChatStore()

// Store reactive references
const {
  activeConversation,
  availableProviders,
  currentProvider,
  currentModel,
  currentProviderData,
  isLoading,
  error,
  connectionStatus,
  hasHealthyProviders,
} = storeToRefs(chatStore)

// Local reactive state
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const textareaRef = ref<HTMLTextAreaElement>()

// Computed properties
const canSend = computed(() => {
  return inputMessage.value.trim().length > 0 && 
         !isLoading.value && 
         hasHealthyProviders.value
})

const connectionStatusClass = computed(() => {
  return `status-${connectionStatus.value}`
})

const connectionStatusText = computed(() => {
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

async function handleProviderChange(providerId: string, modelId?: string) {
  await chatStore.switchProvider({
    targetProvider: providerId,
    targetModel: modelId,
    preserveContext: true,
  })
}

function clearError() {
  chatStore.clearError()
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
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

watch(() => activeConversation.value?.messages.length, () => {
  scrollToBottom()
})

// Lifecycle
onMounted(async () => {
  await chatStore.initialize()
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

.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: #fef2f2;
  border-left: 4px solid #dc2626;
  color: #991b1b;
}

.error-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #991b1b;
  padding: 0;
  margin-left: 1rem;
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

.provider-latency {
  font-size: 0.75rem;
  color: #9ca3af;
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
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
  gap: 0.5rem;
}
</style>