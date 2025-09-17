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
      
      <!-- Model Selection -->
      <div class="p-4 border-b border-cyan-900/30">
        <div class="text-cyan-600 text-xs mb-2">MODEL SELECT</div>
        <select 
          v-model="selectedModel"
          class="w-full px-2 py-1.5 bg-black border border-cyan-900/30 text-gray-300 text-xs focus:outline-none focus:border-cyan-500/50"
        >
          <option v-for="model in availableModels" :key="model" :value="model">
            > {{ model }}
          </option>
        </select>
        <div class="mt-2 flex items-center gap-2">
          <div class="flex gap-1">
            <div class="w-1 h-3 bg-green-500"></div>
            <div class="w-1 h-3 bg-green-500"></div>
            <div class="w-1 h-3 bg-green-500"></div>
            <div class="w-1 h-3 bg-gray-700"></div>
            <div class="w-1 h-3 bg-gray-700"></div>
          </div>
          <span class="text-xs text-green-500">ONLINE</span>
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
            <span class="text-cyan-600">UPTIME</span>
            <span class="text-gray-400">{{ sessionTime }}</span>
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
          <span>Powered by Ollama</span>
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
              <div>JUGGLER AI SYSTEM v2.0.0</div>
              <div>================================</div>
              <div>Initializing neural interface...</div>
              <div>Loading language model...</div>
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
                  AI>>>
                </div>
              </div>
              
              <!-- Content -->
              <div class="flex-1">
                <div class="border-l border-cyan-900/30 pl-3">
                  <pre class="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">{{ message.content }}</pre>
                  <div class="mt-1 text-xs text-gray-600 flex items-center gap-3 font-mono">
                    <span>[{{ formatTime(message.id) }}]</span>
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
            <div class="text-yellow-500 text-xs mt-1">AI>>></div>
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
              v-model="inputMessage"
              type="text"
              placeholder="_"
              class="flex-1 bg-transparent text-gray-300 text-sm placeholder-gray-700 focus:outline-none font-mono"
              :disabled="isLoading || !selectedModel"
              @keyup="showCursor = false"
              @blur="showCursor = true"
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

    <!-- Side Indicators -->
    <div class="w-8 bg-zinc-950 border-l border-cyan-900/30 flex flex-col items-center py-4 gap-2">
      <div class="w-1 h-8 bg-cyan-500/50"></div>
      <div class="w-1 h-4 bg-green-500"></div>
      <div class="w-1 h-4 bg-green-500"></div>
      <div class="w-1 h-4 bg-green-500/50"></div>
      <div class="flex-1"></div>
      <div class="w-1 h-1 bg-cyan-500 animate-pulse"></div>
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
}

// State
const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const conversationId = ref<string | null>(null)
const availableModels = ref<string[]>([])
const selectedModel = ref('')
const messagesContainer = ref<HTMLElement>()
const currentTitle = ref('')
const conversationHistory = ref<{id: string, title: string}[]>([])
const startTime = ref(Date.now())
const showCursor = ref(true)

// Quick Actions
const quickActions = [
  { label: 'CODE', preview: 'Write functions...', text: 'Write a Python function to ' },
  { label: 'EXPLAIN', preview: 'Break down concepts...', text: 'Explain in simple terms: ' },
  { label: 'DEBUG', preview: 'Analyze problems...', text: 'Help me debug this code: ' }
]

// Computed
const sessionTime = computed(() => {
  const elapsed = Math.floor((Date.now() - startTime.value) / 1000)
  const hours = Math.floor(elapsed / 3600)
  const minutes = Math.floor((elapsed % 3600) / 60)
  const seconds = elapsed % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

// API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

onMounted(async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/providers`)
    const ollama = response.data.providers.ollama
    if (ollama && ollama.available) {
      availableModels.value = ollama.models
      if (ollama.models.length > 0) {
        selectedModel.value = ollama.models[0]
      }
    }
  } catch (error) {
    console.error('Failed to fetch providers:', error)
  }
  
  setInterval(() => {
    startTime.value = startTime.value
  }, 1000)
})

const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedModel.value) return

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
      provider: 'ollama',
      model: selectedModel.value,
      conversation_id: conversationId.value
    })

    if (!conversationId.value) {
      conversationId.value = response.data.conversation_id
    }

    messages.value.push({
      id: response.data.message_id,
      role: 'assistant',
      content: response.data.response
    })

    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed:', error)
    messages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: '[ERROR] Connection failed. Check system status.'
    })
  } finally {
    isLoading.value = false
  }
}

const startNewChat = () => {
  // Save current chat to history if it has messages
  if (messages.value.length > 0 && currentTitle.value) {
    conversationHistory.value.unshift({
      id: conversationId.value || Date.now().toString(),
      title: currentTitle.value
    })
    // Keep only last 10 conversations
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
/* UI stays mono, but messages get better font */
* {
  font-family: 'Courier New', monospace;
}

/* Better readability for actual chat content */
pre.message-content {
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

/* Terminal cursor effect */
input::placeholder {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>