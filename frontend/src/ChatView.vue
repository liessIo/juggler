<!-- frontend/src/ChatView.vue -->
<template>
  <div class="min-h-screen bg-black flex text-gray-300">
    <!-- Sidebar -->
    <div class="w-72 bg-zinc-950 border-r border-zinc-800 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-zinc-800">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h1 class="text-gray-100 font-semibold text-base">JUGGLER</h1>
            <p class="text-cyan-500 text-xs">System Active</p>
          </div>
        </div>
        
        <button 
          @click="startNewChat"
          class="w-full px-3 py-2 bg-gradient-to-r from-cyan-600/10 to-cyan-500/10 border border-cyan-600/30 hover:border-cyan-500 hover:bg-cyan-600/20 text-cyan-400 text-sm font-medium rounded-lg transition-all duration-300"
        >
          New Session
        </button>
        
        <button 
          @click="handleLogout"
          class="w-full px-3 py-2 mt-2 bg-gradient-to-r from-red-600/10 to-red-500/10 border border-red-600/30 hover:border-red-500 hover:bg-red-600/20 text-red-400 text-sm font-medium rounded-lg transition-all duration-300"
        >
          Logout
        </button>
        <button 
          @click="$router.push('/config')"
          class="w-full px-3 py-2 mt-2 bg-gradient-to-r from-cyan-600/10 to-cyan-500/10 border border-cyan-600/30 hover:border-cyan-500 hover:bg-cyan-600/20 text-cyan-400 text-sm font-medium rounded-lg transition-all duration-300"
        >
          Configuration
        </button>
      </div>
      
      <!-- Provider & Model Selection -->
      <div class="p-4 border-b border-zinc-800">
        <!-- Provider Select -->
        <div class="text-cyan-500 text-xs font-medium mb-2 uppercase tracking-wide">Provider</div>
        <select 
          v-if="Object.keys(filteredProviders).length > 0"
          v-model="selectedProvider"
          @change="onProviderChange"
          class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 hover:border-cyan-500/50 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 text-gray-300 text-sm rounded-lg transition-all duration-200 outline-none mb-3"
        >
          <option v-for="(provider, key) in filteredProviders" :key="key" :value="key">
            {{ key.toUpperCase() }}
          </option>
        </select>
        
        <!-- No Providers Message -->
        <div v-else class="mb-3">
          <div class="px-3 py-2 bg-yellow-900/20 border border-yellow-600/30 rounded-lg text-xs text-yellow-500">
            No providers configured
          </div>
          <button 
            @click="$router.push('/config?tab=models')"
            class="mt-2 text-xs text-cyan-500 hover:text-cyan-400 transition-colors"
          >
            → Configure in settings
          </button>
        </div>
        
        <!-- Model Select with Refresh -->
        <div class="flex items-center gap-2 mb-2">
          <div class="text-cyan-500 text-xs font-medium uppercase tracking-wide">Model</div>
          <button 
            @click="refreshProviders"
            class="ml-auto text-cyan-500 hover:text-cyan-400 text-sm transition-colors"
            title="Configure models"
          >
            ⚙
          </button>
        </div>
        
        <select 
          v-model="selectedModel"
          @change="saveLastUsedModel"
          :disabled="!availableModels.length"
          class="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 hover:border-cyan-500/50 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 text-gray-300 text-sm rounded-lg transition-all duration-200 outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <option v-if="!availableModels.length" value="">No models selected</option>
          <option v-for="model in availableModels" :key="model" :value="model">
            {{ model }}
          </option>
        </select>
        
        <!-- Link to config if no models -->
        <div v-if="selectedProvider && availableModels.length === 0" class="mt-2">
          <button 
            @click="$router.push('/config?tab=models')"
            class="text-xs text-cyan-500 hover:text-cyan-400 transition-colors"
          >
            → Configure models in settings
          </button>
        </div>
        
        <!-- Provider Status -->
        <div class="mt-3 flex items-center gap-2">
          <div class="flex gap-1">
            <div v-for="i in 5" :key="i" 
                 :class="['w-1 h-2.5 rounded-sm transition-all', i <= providerStatus ? 'bg-green-500' : 'bg-zinc-700']"></div>
          </div>
          <span class="text-xs font-medium" :class="providerStatusColor">
            {{ providerStatusText }}
          </span>
        </div>
        
        <!-- Model Count -->
        <div class="mt-2 text-xs text-zinc-500">
          Available models: {{ availableModels.length }}
        </div>
      </div>

      <!-- System Stats -->
      <div class="flex-1 p-4 space-y-3 overflow-y-auto">
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-cyan-500 font-medium uppercase tracking-wide">Messages</span>
            <span class="text-zinc-400 font-mono">{{ messages.length.toString().padStart(3, '0') }}</span>
          </div>
          <div class="h-px bg-zinc-800"></div>
        </div>
        
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-cyan-500 font-medium uppercase tracking-wide">Provider</span>
            <span class="text-zinc-400">{{ selectedProvider?.toUpperCase() || 'NONE' }}</span>
          </div>
          <div class="h-px bg-zinc-800"></div>
        </div>
        
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-cyan-500 font-medium uppercase tracking-wide">Status</span>
            <span :class="isLoading ? 'text-yellow-500' : 'text-green-500'">
              {{ isLoading ? 'Processing' : 'Ready' }}
            </span>
          </div>
          <div class="h-px bg-zinc-800"></div>
        </div>

        <!-- Conversation History -->
        <div class="mt-6">
          <div class="text-cyan-500 text-xs font-medium uppercase tracking-wide mb-3">Recent Sessions</div>
          <div class="space-y-1">
            <div 
              v-for="conv in conversationHistory" 
              :key="conv.id"
              @click="loadConversation(conv.id)"
              :class="[
                'px-3 py-2 text-xs hover:text-gray-300 hover:bg-zinc-900 cursor-pointer truncate rounded-lg transition-all',
                conversationId === conv.id ? 'text-cyan-400 bg-zinc-900 border-l-2 border-cyan-500' : 'text-zinc-500'
              ]"
            >
              {{ conv.title }}
            </div>
            <div v-if="conversationHistory.length === 0" class="text-xs text-zinc-600 px-3 py-2">
              No previous sessions
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-zinc-800">
        <div class="flex items-center gap-2 text-xs text-zinc-600">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Powered by {{ selectedProvider || 'AI' }}</span>
        </div>
      </div>
    </div>

    <!-- Main Panel -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <div class="h-14 bg-zinc-950 border-b border-zinc-800 flex items-center px-6">
        <div class="flex items-center gap-2 text-sm">
          <span class="text-cyan-500 font-medium">Session:</span>
          <span class="text-zinc-400">{{ currentTitle || 'New Session' }}</span>
        </div>
        <div class="ml-auto flex items-center gap-4">
          <div v-if="selectedModel" class="text-xs text-zinc-500 font-mono">
            {{ selectedProvider?.toUpperCase() }} :: {{ selectedModel }}
          </div>
          <div v-if="isLoading" class="flex items-center gap-2">
            <div class="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
            <span class="text-xs text-yellow-500 font-medium">Processing</span>
          </div>
        </div>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto bg-zinc-950/50" ref="messagesContainer">
        <div class="max-w-4xl mx-auto p-6">
          <!-- Boot Screen -->
          <div v-if="messages.length === 0" class="space-y-6">
            <div class="text-center space-y-4 py-12">
              <div class="w-16 h-16 mx-auto bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-2xl flex items-center justify-center">
                <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h2 class="text-2xl font-semibold text-gray-100">Juggler AI v2.1</h2>
              <p class="text-zinc-500 text-sm">Multi-provider AI chat system</p>
              <div class="flex items-center justify-center gap-6 text-xs text-zinc-600">
                <div>{{ Object.keys(filteredProviders).length }} providers</div>
                <div>•</div>
                <div>{{ totalModels }} models</div>
                <div>•</div>
                <div class="text-green-500">System ready</div>
              </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="grid grid-cols-3 gap-3 mt-8">
              <button 
                v-for="action in quickActions" 
                :key="action.text"
                @click="inputMessage = action.text; sendMessage()"
                class="p-4 bg-zinc-900 border border-zinc-800 hover:border-cyan-500/50 hover:bg-zinc-900/70 rounded-lg transition-all text-left group"
              >
                <div class="text-cyan-500 text-xs font-medium mb-1.5 group-hover:text-cyan-400 transition-colors">{{ action.label }}</div>
                <div class="text-zinc-500 text-xs">{{ action.preview }}</div>
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-for="message in messages" :key="message.id" class="mb-6">
            <div class="flex items-start gap-4">
              <!-- Avatar -->
              <div class="mt-1">
                <div v-if="message.role === 'user'" 
                     class="w-8 h-8 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center text-white text-xs font-semibold">
                  U
                </div>
                <div v-else 
                     class="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center text-white text-xs font-semibold">
                  AI
                </div>
              </div>
              
              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                  <div class="prose prose-invert max-w-none">
                    <pre class="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed m-0">{{ message.content }}</pre>
                  </div>
                  <div class="mt-3 pt-3 border-t border-zinc-800 flex items-center gap-4 text-xs text-zinc-600">
                    <span>{{ formatTime(message) }}</span>
                    <span v-if="message.model" class="text-zinc-700">{{ message.model }}</span>
                    <button 
                      v-if="message.role === 'assistant'" 
                      @click="copyToClipboard(message.content)"
                      class="ml-auto text-cyan-600/50 hover:text-cyan-500 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="flex items-start gap-4">
            <div class="w-8 h-8 bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-lg flex items-center justify-center">
              <div class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            </div>
            <div class="flex-1">
              <div class="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <span class="text-yellow-500 text-sm">
                  Processing your request...
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="border-t border-zinc-800 bg-zinc-950 p-4">
        <div class="max-w-4xl mx-auto">
          <form @submit.prevent="sendMessage" class="flex items-center gap-3">
            <input
              ref="inputField"
              v-model="inputMessage"
              type="text"
              placeholder="Type your message..."
              class="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 hover:border-zinc-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 text-gray-300 text-sm rounded-lg transition-all outline-none"
              :disabled="isLoading || !selectedModel"
            />
            <button
              type="submit"
              :disabled="isLoading || !inputMessage.trim() || !selectedModel"
              class="px-6 py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:from-zinc-800 disabled:to-zinc-800 text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
          <div v-if="!selectedModel" class="mt-2 text-xs text-yellow-500">
            Please select a model to start chatting
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Component name for keep-alive
import { defineOptions } from 'vue'
defineOptions({ name: 'Chat' })

import { ref, onMounted, nextTick, computed } from 'vue'
import api from './utils/axios'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

// Auth
const authStore = useAuthStore()
const router = useRouter()

// Types
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  provider?: string
  model?: string
  timestamp: number
}

interface Provider {
  available: boolean
  models: string[]
}

// State
const messages = ref<Message[]>([])
const inputMessage = ref('')
const inputField = ref<HTMLInputElement>()
const isLoading = ref(false)
const isRefreshing = ref(false)
const conversationId = ref<string | null>(null)
const providers = ref<Record<string, Provider>>({})
const selectedProvider = ref<string>('')
const availableModels = ref<string[]>([])
const selectedModel = ref('')
const messagesContainer = ref<HTMLElement>()
const currentTitle = ref('')
const conversationHistory = ref<{id: string, title: string}[]>([])
const startTime = ref(Date.now())

// Quick Actions
const quickActions = [
  { label: 'CODE', preview: 'Write functions...', text: 'Write a Python function to ' },
  { label: 'EXPLAIN', preview: 'Break down concepts...', text: 'Explain in simple terms: ' },
  { label: 'DEBUG', preview: 'Analyze problems...', text: 'Help me debug this code: ' }
]

// Computed
const filteredProviders = computed(() => {
  const filtered: Record<string, Provider> = {}
  for (const [key, provider] of Object.entries(providers.value)) {
    if (provider.available && provider.models.length > 0) {
      filtered[key] = provider
    }
  }
  return filtered
})

const providerStatus = computed(() => {
  if (!selectedProvider.value) return 0
  const provider = providers.value[selectedProvider.value]
  if (!provider) return 0
  if (!provider.available) return 1
  if (provider.models.length === 0) return 2
  if (provider.models.length < 3) return 3
  if (provider.models.length < 10) return 4
  return 5
})

const providerStatusText = computed(() => {
  if (!selectedProvider.value) return 'No Provider'
  const provider = providers.value[selectedProvider.value]
  if (!provider) return 'Unknown'
  if (!provider.available) return 'Offline'
  if (provider.models.length === 0) return 'No Models'
  return 'Online'
})

const providerStatusColor = computed(() => {
  if (providerStatus.value === 0) return 'text-zinc-600'
  if (providerStatus.value === 1) return 'text-red-500'
  if (providerStatus.value < 3) return 'text-yellow-500'
  return 'text-green-500'
})

const totalModels = computed(() => {
  return Object.values(filteredProviders.value).reduce((sum, p) => sum + p.models.length, 0)
})

// LocalStorage keys for last-used models
const LAST_USED_MODEL_KEY = 'juggler_last_used_models'

// Functions
const loadLastUsedModel = () => {
  try {
    const saved = localStorage.getItem(LAST_USED_MODEL_KEY)
    if (saved) {
      const lastUsed = JSON.parse(saved)
      const provider = selectedProvider.value
      if (provider && lastUsed[provider] && availableModels.value.includes(lastUsed[provider])) {
        selectedModel.value = lastUsed[provider]
      }
    }
  } catch (e) {
    console.error('Failed to load last used model:', e)
  }
}

const saveLastUsedModel = () => {
  try {
    const saved = localStorage.getItem(LAST_USED_MODEL_KEY)
    const lastUsed = saved ? JSON.parse(saved) : {}
    lastUsed[selectedProvider.value] = selectedModel.value
    localStorage.setItem(LAST_USED_MODEL_KEY, JSON.stringify(lastUsed))
  } catch (e) {
    console.error('Failed to save last used model:', e)
  }
}

const fetchEnabledModels = async () => {
  try {
    const response = await api.get('/api/config/models/enabled')
    
    // Transform API response to expected format
    const apiProviders = response.data.providers || {}
    const transformed: Record<string, Provider> = {}
    
    for (const [providerKey, providerData] of Object.entries(apiProviders)) {
      transformed[providerKey] = {
        available: true,
        models: (providerData as any).models || []
      }
    }
    
    providers.value = transformed
    
    // Auto-select first available provider if none selected
    if (!selectedProvider.value) {
      const availableProvider = Object.keys(filteredProviders.value).find(
        key => filteredProviders.value[key].available && filteredProviders.value[key].models.length > 0
      )
      if (availableProvider) {
        selectedProvider.value = availableProvider
        onProviderChange()
      }
    }
  } catch (error) {
    console.error('Failed to fetch enabled models:', error)
  }
}

const fetchConversations = async () => {
  try {
    const response = await api.get('/api/chat/conversations')
    conversationHistory.value = response.data.conversations.map((conv: any) => ({
      id: conv.id,
      title: conv.title,
      created_at: conv.created_at,
      message_count: conv.message_count
    }))
  } catch (error) {
    console.error('Failed to fetch conversations:', error)
  }
}

const loadConversation = async (convId: string) => {
  try {
    // Load messages from this conversation
    const response = await api.get(`/api/chat/conversations/${convId}/messages`)
    
    // Clear current chat
    messages.value = []
    conversationId.value = convId
    
    // Load messages with proper timestamp
    messages.value = response.data.messages.map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      provider: msg.provider,
      model: msg.model,
      timestamp: new Date(msg.timestamp).getTime()
    }))
    
    // Set title from first message
    if (messages.value.length > 0) {
      const firstUserMsg = messages.value.find(m => m.role === 'user')
      currentTitle.value = firstUserMsg ? firstUserMsg.content.slice(0, 30).toUpperCase() : 'LOADED SESSION'
    }
    
    // Scroll to bottom
    await nextTick()
    scrollToBottom()
    
  } catch (error) {
    console.error('Failed to load conversation:', error)
  }
}

const refreshProviders = async () => {
  // Redirect to config for model management
  router.push('/config?tab=models')
}

const onProviderChange = () => {
  const provider = providers.value[selectedProvider.value]
  if (provider && provider.available) {
    availableModels.value = provider.models
    if (provider.models.length > 0) {
      // Try to load last-used model first
      loadLastUsedModel()
      
      // If no last-used or not available, pick a good default
      if (!selectedModel.value || !availableModels.value.includes(selectedModel.value)) {
        const preferredModels = ['claude-3.5-sonnet', 'llama-3.3-70b', 'phi3:medium']
        const defaultModel = provider.models.find(m => 
          preferredModels.some(pref => m.includes(pref))
        ) || provider.models[0]
        selectedModel.value = defaultModel
      }
    } else {
      selectedModel.value = ''
    }
  } else {
    availableModels.value = []
    selectedModel.value = ''
  }
}

// Lifecycle
onMounted(async () => {
  await fetchEnabledModels()
  await fetchConversations()
})

// Message handling
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedModel.value || !selectedProvider.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    timestamp: Date.now()
  }
  
  messages.value.push(userMessage)
  
  if (!currentTitle.value) {
    currentTitle.value = inputMessage.value.slice(0, 30).toUpperCase()
  }
  
  const messageText = inputMessage.value
  inputMessage.value = ''
  isLoading.value = true

  await nextTick()
  scrollToBottom()

  try {
    const response = await api.post('/api/chat/send', {
      message: messageText,
      provider: selectedProvider.value,
      model: selectedModel.value,
      conversation_id: conversationId.value
    })

    if (!conversationId.value) {
      conversationId.value = response.data.conversation_id
      // Refresh conversation list after first message
      await fetchConversations()
    }

    messages.value.push({
      id: response.data.message_id,
      role: 'assistant',
      content: response.data.response,
      provider: selectedProvider.value,
      model: selectedModel.value,
      timestamp: Date.now()
    })

    await nextTick()
    scrollToBottom()
  } catch (error: any) {
    console.error('Failed:', error)
    const errorMsg = error.response?.data?.detail || 'Connection failed. Check system status.'
    messages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: `[ERROR] ${errorMsg}`,
      provider: selectedProvider.value,
      timestamp: Date.now()
    })
  } finally {
    isLoading.value = false
    // UX FIX: Auto-focus input field after sending
    await nextTick()
    inputField.value?.focus()
  }
}

const startNewChat = () => {
  messages.value = []
  conversationId.value = null
  inputMessage.value = ''
  currentTitle.value = ''
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const copyToClipboard = async (text: string) => {
  await navigator.clipboard.writeText(text)
}

const formatTime = (message: Message) => {
  const timestamp = message.timestamp || Date.now()
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
* {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #18181b;
}
::-webkit-scrollbar-thumb {
  background: #3f3f46;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #52525b;
}

.prose pre {
  background: transparent;
  padding: 0;
  margin: 0;
}
</style>