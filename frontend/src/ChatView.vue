<!-- frontend/src/ChatView.vue -->
<template>
  <div class="min-h-screen bg-black flex text-gray-300 font-mono">
    <!-- Sidebar -->
    <div class="w-72 bg-zinc-950 border-r border-cyan-900/30 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-cyan-900/30">
        <div class="flex items-center gap-3 mb-4">
          <div class="relative">
            <div class="w-8 h-8 border border-cyan-500/50 flex items-center justify-center">
              <div class="w-1 h-4 bg-cyan-500"></div>
              <div class="w-4 h-1 bg-cyan-500 absolute"></div>
            </div>
            <div class="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-green-500"></div>
          </div>
          <div>
            <h1 class="text-gray-100 font-bold text-sm tracking-wider">JUGGLER</h1>
            <p class="text-cyan-600 text-xs">SYSTEM ACTIVE</p>
          </div>
        </div>
        
        <button 
          @click="startNewChat"
          class="w-full px-3 py-2 bg-zinc-900 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs tracking-wider transition-all"
        >
          [+] NEW SESSION
        </button>
        
        <button 
          @click="handleLogout"
          class="w-full px-3 py-2 mt-2 bg-red-900/20 border border-red-900/30 hover:border-red-500/50 text-red-400 text-xs tracking-wider transition-all"
        >
          [LOGOUT]
        </button>
        <button 
          @click="$router.push('/config')"
          class="w-full px-3 py-2 mt-2 bg-zinc-900 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs tracking-wider transition-all"
        >
          [CONFIG]
        </button>
      </div>
      
      <!-- Provider & Model Selection -->
      <div class="p-4 border-b border-cyan-900/30">
        <!-- Provider Select -->
        <div class="text-cyan-600 text-xs mb-2">PROVIDER SELECT</div>
        <select 
          v-if="Object.keys(filteredProviders).length > 0"
          v-model="selectedProvider"
          @change="onProviderChange"
          class="w-full px-2 py-1.5 bg-black border border-cyan-900/30 text-gray-300 text-xs focus:outline-none focus:border-cyan-500/50 mb-3"
        >
          <option v-for="(provider, key) in filteredProviders" :key="key" :value="key">
            > {{ key.toUpperCase() }} ✓
          </option>
        </select>
        
        <!-- No Providers Message -->
        <div v-else class="mb-3">
          <div class="px-2 py-3 bg-zinc-900 border border-yellow-900/30 text-xs text-yellow-500">
            No providers configured
          </div>
          <button 
            @click="$router.push('/config?tab=models')"
            class="mt-2 text-xs text-cyan-500 hover:text-cyan-400"
          >
            → Select models in configuration
          </button>
        </div>
        
        <!-- Model Select with Refresh -->
        <div class="flex items-center gap-2 mb-2">
          <div class="text-cyan-600 text-xs">MODEL SELECT</div>
          <button 
            @click="refreshProviders"
            class="ml-auto text-cyan-500 hover:text-cyan-400 text-xs"
            title="Configure models"
          >
            ⚙
          </button>
        </div>
        
        <select 
          v-model="selectedModel"
          @change="saveLastUsedModel"
          :disabled="!availableModels.length"
          class="w-full px-2 py-1.5 bg-black border border-cyan-900/30 text-gray-300 text-xs focus:outline-none focus:border-cyan-500/50"
        >
          <option v-if="!availableModels.length" value="">No models selected</option>
          <option v-for="model in availableModels" :key="model" :value="model">
            > {{ model }}
          </option>
        </select>
        
        <!-- Link to config if no models -->
        <div v-if="selectedProvider && availableModels.length === 0" class="mt-2">
          <button 
            @click="$router.push('/config?tab=models')"
            class="text-xs text-cyan-500 hover:text-cyan-400"
          >
            → Configure models in settings
          </button>
        </div>
        
        <!-- Provider Status -->
        <div class="mt-3 flex items-center gap-2">
          <div class="flex gap-1">
            <div v-for="i in 5" :key="i" 
                 :class="['w-1 h-3', i <= providerStatus ? 'bg-green-500' : 'bg-gray-700']"></div>
          </div>
          <span class="text-xs" :class="providerStatusColor">
            {{ providerStatusText }}
          </span>
        </div>
        
        <!-- Model Count -->
        <div class="mt-2 text-xs text-gray-600">
          Models: {{ availableModels.length }}
        </div>
      </div>

      <!-- System Stats -->
      <div class="flex-1 p-4 space-y-3">
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-cyan-600">MESSAGES</span>
            <span class="text-gray-400">[{{ messages.length.toString().padStart(3, '0') }}]</span>
          </div>
          <div class="h-px bg-cyan-900/30"></div>
        </div>
        
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-cyan-600">PROVIDER</span>
            <span class="text-gray-400">{{ selectedProvider?.toUpperCase() || 'NONE' }}</span>
          </div>
          <div class="h-px bg-cyan-900/30"></div>
        </div>
        
        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-cyan-600">STATUS</span>
            <span :class="isLoading ? 'text-yellow-500' : 'text-green-500'">
              {{ isLoading ? 'PROCESSING' : 'READY' }}
            </span>
          </div>
          <div class="h-px bg-cyan-900/30"></div>
        </div>

        <!-- Conversation History -->
        <div class="mt-6">
          <div class="text-cyan-600 text-xs mb-3">RECENT SESSIONS</div>
          <div class="space-y-1">
            <div v-for="conv in conversationHistory" :key="conv.id"
                 class="px-2 py-1 text-xs text-gray-500 hover:text-gray-300 hover:bg-zinc-900 cursor-pointer truncate">
              > {{ conv.title }}
            </div>
            <div v-if="conversationHistory.length === 0" class="text-xs text-gray-700">
              No history
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-cyan-900/30">
        <div class="flex items-center gap-2 text-xs text-gray-600">
          <i class="pi pi-server"></i>
          <span>Powered by {{ selectedProvider || 'AI' }}</span>
        </div>
      </div>
    </div>

    <!-- Main Panel -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <div class="h-12 bg-zinc-950 border-b border-cyan-900/30 flex items-center px-4">
        <div class="flex items-center gap-2 text-xs">
          <span class="text-cyan-600">SESSION:</span>
          <span class="text-gray-400">{{ currentTitle || 'NEW SESSION' }}</span>
        </div>
        <div class="ml-auto flex items-center gap-4">
          <div v-if="selectedModel" class="text-xs text-gray-500">
            [{{ selectedProvider?.toUpperCase() }}::{{ selectedModel }}]
          </div>
          <div v-if="isLoading" class="flex items-center gap-2">
            <div class="w-2 h-2 bg-yellow-500 animate-pulse"></div>
            <span class="text-xs text-yellow-500">PROCESSING</span>
          </div>
        </div>
      </div>

      <!-- Terminal Output -->
      <div class="flex-1 overflow-y-auto bg-zinc-950/50" ref="messagesContainer">
        <div class="max-w-4xl mx-auto p-6">
          <!-- Boot Screen -->
          <div v-if="messages.length === 0" class="space-y-6">
            <div class="text-green-500/80 text-xs space-y-1">
              <div>JUGGLER AI SYSTEM v2.0.6</div>
              <div>================================</div>
              <div>Initializing neural interface...</div>
              <div>Loading language models...</div>
              <div>{{ Object.keys(filteredProviders).length }} providers available</div>
              <div>{{ totalModels }} models loaded</div>
              <div>System ready.</div>
              <div class="pt-4 text-cyan-500">
                > Type command or query to begin_
              </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="grid grid-cols-3 gap-3 mt-8">
              <button 
                v-for="action in quickActions" 
                :key="action.text"
                @click="inputMessage = action.text; sendMessage()"
                class="p-3 bg-zinc-900 border border-cyan-900/30 hover:border-cyan-500/50 transition-all text-left"
              >
                <div class="text-cyan-500 text-xs mb-1">[{{ action.label }}]</div>
                <div class="text-gray-400 text-xs">{{ action.preview }}</div>
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-for="message in messages" :key="message.id" class="mb-4">
            <div class="flex items-start gap-3">
              <!-- Indicator -->
              <div class="mt-1">
                <div v-if="message.role === 'user'" class="text-cyan-500 text-xs">
                  USER>
                </div>
                <div v-else class="text-green-500 text-xs">
                  {{ message.provider || 'AI' }}>>>
                </div>
              </div>
              
              <!-- Content -->
              <div class="flex-1">
                <div class="border-l border-cyan-900/30 pl-3">
                  <pre class="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{{ message.content }}</pre>
                  <div class="mt-1 text-xs text-gray-600 flex items-center gap-3 font-mono">
                    <span>[{{ formatTime(message.id) }}]</span>
                    <span v-if="message.model" class="text-gray-700">[{{ message.model }}]</span>
                    <button 
                      v-if="message.role === 'assistant'" 
                      @click="copyToClipboard(message.content)"
                      class="text-cyan-600/50 hover:text-cyan-500"
                    >
                      COPY
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="flex items-start gap-3">
            <div class="text-yellow-500 text-xs mt-1">{{ selectedProvider?.toUpperCase() }}>>></div>
            <div class="flex-1">
              <div class="border-l border-cyan-900/30 pl-3">
                <span class="text-yellow-500 text-sm">
                  Processing<span class="animate-pulse">...</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Command Input -->
      <div class="border-t border-cyan-900/30 bg-zinc-950 p-4">
        <div class="max-w-4xl mx-auto">
          <form @submit.prevent="sendMessage" class="flex items-center gap-2">
            <span class="text-cyan-500 text-sm">></span>
            <input
              ref="inputField"
              v-model="inputMessage"
              type="text"
              placeholder="_"
              class="flex-1 bg-transparent text-gray-300 text-sm placeholder-gray-700 focus:outline-none font-mono"
              :disabled="isLoading || !selectedModel"
            />
            <button
              type="submit"
              :disabled="isLoading || !inputMessage.trim() || !selectedModel"
              class="px-3 py-1 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-500 text-xs disabled:opacity-30 disabled:cursor-not-allowed"
            >
              [SEND]
            </button>
          </form>
          <div v-if="!selectedModel" class="mt-2 text-xs text-yellow-500">
            WARNING: No model selected
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import axios from 'axios'
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
  if (!selectedProvider.value) return 'NO PROVIDER'
  const provider = providers.value[selectedProvider.value]
  if (!provider) return 'UNKNOWN'
  if (!provider.available) return 'OFFLINE'
  if (provider.models.length === 0) return 'NO MODELS'
  return 'ONLINE'
})

const providerStatusColor = computed(() => {
  if (providerStatus.value === 0) return 'text-gray-700'
  if (providerStatus.value === 1) return 'text-red-500'
  if (providerStatus.value < 3) return 'text-yellow-500'
  return 'text-green-500'
})

const totalModels = computed(() => {
  return Object.values(filteredProviders.value).reduce((sum, p) => sum + p.models.length, 0)
})

// API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
    const response = await axios.get(`${API_BASE_URL}/api/config/models/enabled`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    providers.value = response.data.providers
    
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
})

// Message handling
const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedModel.value || !selectedProvider.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value
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
    const response = await axios.post(`${API_BASE_URL}/api/chat/send`, {
      message: messageText,
      provider: selectedProvider.value,
      model: selectedModel.value,
      conversation_id: conversationId.value
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (!conversationId.value) {
      conversationId.value = response.data.conversation_id
    }

    messages.value.push({
      id: response.data.message_id,
      role: 'assistant',
      content: response.data.response,
      provider: selectedProvider.value,
      model: selectedModel.value
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
      provider: selectedProvider.value
    })
  } finally {
    isLoading.value = false
    // UX FIX: Auto-focus input field after sending
    await nextTick()
    inputField.value?.focus()
  }
}

const startNewChat = () => {
  if (messages.value.length > 0 && currentTitle.value) {
    conversationHistory.value.unshift({
      id: conversationId.value || Date.now().toString(),
      title: currentTitle.value
    })
    if (conversationHistory.value.length > 10) {
      conversationHistory.value.pop()
    }
  }
  
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

const formatTime = (id: string) => {
  const date = new Date(parseInt(id))
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
* {
  font-family: 'Courier New', monospace;
}

pre {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: #000;
}
::-webkit-scrollbar-thumb {
  background: #0e7490;
  opacity: 0.5;
}

input::placeholder {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>