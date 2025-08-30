
<template>
  <!-- 
    File: src/components/MessageBubble.vue
    Individual message display component
    Shows chat messages with metadata and formatting
  -->

  <div 
    class="message-bubble" 
    :class="[
      `message-${message.role}`,
      { 'message-error': message.error },
      { 'compact': compact }
    ]"
  >
    <div class="message-content">
      <div v-if="message.role === 'system'" class="system-message">
        <div class="system-icon">ⓘ</div>
        <div class="system-text">{{ message.content }}</div>
      </div>
      
      <div v-else class="chat-message">
        <div class="message-text" v-html="formattedContent"></div>
      </div>
    </div>
    
    <div v-if="showMetadata && !compact" class="message-metadata">
      <div class="metadata-row">
        <div class="provider-info">
          <span class="provider-badge" :style="{ backgroundColor: providerColor }">
            {{ getProviderDisplayName(message.provider) }}
          </span>
          <span class="model-name">{{ message.model }}</span>
        </div>
        
        <div class="timestamp">
          {{ formatTimestamp(message.timestamp) }}
        </div>
      </div>
      
      <div v-if="message.latency_ms || message.tokens" class="performance-info">
        <span v-if="message.latency_ms" class="latency">
          ⏱ {{ formatLatency(message.latency_ms) }}
        </span>
        <span v-if="message.tokens" class="token-count">
          📊 {{ message.tokens.input + message.tokens.output }} tokens
          <span class="token-breakdown">
            ({{ message.tokens.input }}→{{ message.tokens.output }})
          </span>
        </span>
      </div>
    </div>
    
    <!-- Error details -->
    <div v-if="message.error" class="error-details">
      <div class="error-icon">⚠</div>
      <div class="error-text">{{ message.error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '@/types/chat'

interface Props {
  message: ChatMessage
  showMetadata?: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showMetadata: true,
  compact: false
})

// Computed properties
const providerColor = computed(() => {
  const colors: Record<string, string> = {
    'ollama': '#10B981',
    'groq': '#8B5CF6', 
    'gemini': '#3B82F6',
    'openai': '#EF4444',
  }
  return colors[props.message.provider] || '#6B7280'
})

const formattedContent = computed(() => {
  // Convert markdown-like formatting to HTML
  let content = props.message.content
  
  // Convert **bold** to <strong>
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Convert `code` to <code>
  content = content.replace(/`([^`]+)`/g, '<code>$1</code>')
  
  // Convert ```code blocks``` to <pre><code>
  content = content.replace(/```(\w+)?\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
  
  // Convert line breaks to <br>
  content = content.replace(/\n/g, '<br>')
  
  return content
})

// Helper functions
function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function getProviderDisplayName(providerId: string): string {
  const displayNames: Record<string, string> = {
    'ollama': 'Ollama',
    'groq': 'Groq',
    'gemini': 'Gemini',
    'openai': 'OpenAI',
  }
  return displayNames[providerId] || providerId
}
</script>

<style scoped>
.message-bubble {
  margin-bottom: 1.5rem;
  animation: fadeIn 0.3s ease-out;
}

.message-bubble.compact {
  margin-bottom: 0.75rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-content {
  margin-bottom: 0.5rem;
}

/* User messages */
.message-user .chat-message {
  margin-left: 2rem;
}

.message-user .message-text {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 18px 18px 4px 18px;
  display: inline-block;
  max-width: 85%;
  margin-left: auto;
  float: right;
  clear: both;
}

/* Assistant messages */
.message-assistant .chat-message {
  margin-right: 2rem;
}

.message-assistant .message-text {
  background: white;
  color: #374151;
  padding: 0.75rem 1rem;
  border-radius: 18px 18px 18px 4px;
  display: inline-block;
  max-width: 85%;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* System messages */
.message-system {
  margin: 1rem 0;
}

.system-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f3f4f6;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  font-size: 0.875rem;
  color: #6b7280;
  border-left: 3px solid #9ca3af;
}

.system-icon {
  font-size: 1rem;
  opacity: 0.7;
}

.system-text {
  flex: 1;
}

/* Error messages */
.message-error .message-text {
  background: #fef2f2 !important;
  border-color: #fecaca !important;
  color: #991b1b !important;
}

.error-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #991b1b;
}

.error-icon {
  font-size: 1rem;
}

/* Message metadata */
.message-metadata {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.metadata-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.provider-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.provider-badge {
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.model-name {
  font-weight: 500;
  color: #4b5563;
}

.timestamp {
  color: #9ca3af;
}

.performance-info {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.latency {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.token-count {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.token-breakdown {
  color: #9ca3af;
  font-size: 0.6875rem;
}

/* Text formatting */
.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.125rem 0.25rem;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875em;
}

.message-assistant .message-text :deep(code) {
  background: #f3f4f6;
}

.message-text :deep(pre) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.75rem;
  margin: 0.5rem 0;
  overflow-x: auto;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.875rem;
  line-height: 1.5;
}

.message-user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-user .message-text :deep(pre) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.message-user .message-text :deep(pre code) {
  color: rgba(255, 255, 255, 0.9);
}

/* Responsive design */
@media (max-width: 768px) {
  .message-user .chat-message,
  .message-assistant .chat-message {
    margin-left: 0.5rem;
    margin-right: 0.5rem;
  }
  
  .message-text {
    max-width: 95% !important;
  }
  
  .metadata-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .performance-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>