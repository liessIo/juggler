<!-- frontend/src/views/ChatView.vue -->
<template>
  <div class="h-screen w-screen bg-black flex overflow-hidden">
    <!-- LEFT SIDEBAR -->
    <div class="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col overflow-hidden">
      <div class="flex-shrink-0 p-3 border-b border-zinc-800">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-8 h-8 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded flex items-center justify-center">
            <span class="text-white text-xs font-bold">J</span>
          </div>
          <div>
            <h1 class="text-gray-100 font-semibold text-sm">JUGGLER</h1>
            <p class="text-cyan-500 text-xs">v3.0</p>
          </div>
        </div>
        <button 
          @click="startNewChat"
          class="w-full px-2 py-1.5 bg-cyan-600/20 border border-cyan-600/30 hover:border-cyan-500 text-cyan-400 text-xs font-medium rounded transition-all"
        >
          New Session
        </button>
      </div>

      <div class="flex-shrink-0 p-3 border-b border-zinc-800 space-y-2">
        <div>
          <div class="text-cyan-500 text-xs font-medium mb-1 uppercase">Provider</div>
          <select 
            v-model="selectedProvider"
            @change="onProviderChange"
            class="w-full px-2 py-1 bg-zinc-900 border border-zinc-700 hover:border-cyan-500/50 focus:border-cyan-500 text-gray-300 text-xs rounded transition-all outline-none"
          >
            <option v-for="(provider, key) in filteredProviders" :key="key" :value="key">
              {{ key.toUpperCase() }}
            </option>
          </select>
        </div>

        <div>
          <div class="text-cyan-500 text-xs font-medium mb-1 uppercase">Model</div>
          <select 
            v-model="selectedModel"
            @change="saveLastUsedModel"
            :disabled="!availableModels.length"
            class="w-full px-2 py-1 bg-zinc-900 border border-zinc-700 hover:border-cyan-500/50 focus:border-cyan-500 text-gray-300 text-xs rounded transition-all outline-none disabled:opacity-50"
          >
            <option v-if="!availableModels.length" value="">No models</option>
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <button 
          @click="$router.push('/config')"
          class="w-full px-2 py-1 bg-zinc-900 border border-zinc-700 hover:border-cyan-500/50 text-cyan-400 text-xs font-medium rounded transition-all"
        >
          ⚙ Config
        </button>
      </div>

      <div class="flex-1 min-h-0 flex flex-col overflow-hidden">
        <div class="flex-1 min-h-0 overflow-y-auto p-3 border-b border-zinc-800">
          <div class="text-cyan-500 text-xs font-medium uppercase mb-2">Recent</div>
          <div class="space-y-1">
            <div 
              v-for="conv in conversationHistory" 
              :key="conv.id"
              @click="loadConversation(conv.id)"
              :class="[
                'px-2 py-1 text-xs cursor-pointer rounded transition-all truncate',
                conversationId === conv.id 
                  ? 'text-cyan-400 bg-zinc-900 border-l-2 border-cyan-500' 
                  : 'text-zinc-500 hover:text-gray-300 hover:bg-zinc-900'
              ]"
              :title="conv.title"
            >
              {{ conv.title || 'New Conversation' }}
            </div>
            <div v-if="conversationHistory.length === 0" class="text-xs text-zinc-600 px-2 py-1">
              No conversations
            </div>
          </div>
        </div>

        <div class="flex-shrink-0 p-3 space-y-1.5 text-xs">
          <div class="flex justify-between">
            <span class="text-cyan-500">Messages:</span>
            <span class="text-zinc-400 font-mono">{{ messages.length }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-cyan-500">Provider:</span>
            <span class="text-zinc-400">{{ selectedProvider?.toUpperCase() || '-' }}</span>
          </div>
        </div>
      </div>

      <div class="flex-shrink-0 p-3 border-t border-zinc-800">
        <button 
          @click="handleLogout"
          class="w-full px-2 py-1 bg-red-600/20 border border-red-600/30 hover:border-red-500 text-red-400 text-xs font-medium rounded transition-all"
        >
          Logout
        </button>
      </div>
    </div>

    <!-- RIGHT PANEL -->
    <div class="flex-1 flex flex-col">
      <div class="flex-shrink-0 h-12 bg-zinc-950 border-b border-zinc-800 flex items-center px-4 justify-between">
        <div class="flex items-center gap-3">
          <div class="text-xs text-zinc-500">SESSION</div>
          <div class="text-sm text-gray-300 font-mono">{{ currentTitle || 'New' }}</div>
        </div>
        <div v-if="selectedModel" class="text-xs text-zinc-500 font-mono">
          {{ selectedProvider?.toUpperCase() }} :: {{ selectedModel }}
        </div>
      </div>

      <!-- MESSAGES AREA -->
      <div class="flex-1 min-h-0 overflow-y-auto bg-zinc-950/30" ref="messagesContainer">
        <div class="max-w-4xl mx-auto p-4 space-y-4">
          <!-- Boot Screen -->
          <div v-if="messages.length === 0" class="text-center py-16 space-y-4">
            <div class="text-2xl font-semibold text-gray-100">JUGGLER v3</div>
            <div class="text-xs text-zinc-600">Multi-provider AI chat with Context Engine</div>
          </div>

          <!-- MESSAGES -->
          <div v-for="(message, idx) in messages" :key="message.id">
            <!-- USER MESSAGE -->
            <div v-if="message.role === 'user'" class="flex justify-end">
              <div class="max-w-2xl bg-cyan-600/20 border border-cyan-600/30 rounded px-3 py-2">
                <div class="text-sm text-gray-200">{{ message.content }}</div>
                <div class="text-xs text-zinc-600 mt-1">{{ formatTime(message) }}</div>
              </div>
            </div>

            <!-- ASSISTANT MESSAGE(S) -->
            <div v-else class="flex justify-start">
              <div class="max-w-full w-full">
                <!-- Get variants for this message -->
                <div v-if="!getVariants(message.id) || getVariants(message.id).length === 0">
                  <!-- Single response (full width) -->
                  <div :class="[
                    'rounded px-4 py-3 border',
                    message.is_active !== false
                      ? 'bg-zinc-900 border-zinc-800' 
                      : 'bg-zinc-950 border-zinc-800 opacity-60'
                  ]">
                    <div class="flex justify-between items-start mb-2 pb-2 border-b border-zinc-700">
                      <div class="text-xs font-medium">
                        <span class="text-cyan-500">{{ message.provider?.toUpperCase() || 'N/A' }}</span>
                        <span class="text-zinc-600 mx-1">::</span>
                        <span class="text-cyan-400">{{ message.model || 'N/A' }}</span>
                      </div>
                      <div class="text-xs text-zinc-600">{{ formatTime(message) }}</div>
                    </div>
                    <div class="text-sm text-gray-300 whitespace-pre-wrap mb-3">{{ message.content }}</div>
                    <div class="flex items-center gap-2">
                      <button 
                        @click="copyToClipboard(message.content)"
                        class="text-cyan-600/40 hover:text-cyan-500 text-xs"
                      >
                        Copy
                      </button>
                      <button 
                        @click="showRerunModal(message.id, $event)"
                        :disabled="isLoading"
                        class="text-cyan-500 hover:text-cyan-400 text-xs font-medium disabled:opacity-50"
                      >
                        Rerun
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Multiple responses (with alternatives table) -->
                <div v-else class="space-y-3">
                  <!-- Active response first -->
                  <div class="bg-zinc-900 border border-zinc-800 rounded px-4 py-3">
                    <div class="flex justify-between items-start mb-2 pb-2 border-b border-zinc-700">
                      <div class="text-xs font-medium">
                        <span class="text-cyan-500">{{ message.provider?.toUpperCase() || 'N/A' }}</span>
                        <span class="text-zinc-600 mx-1">::</span>
                        <span class="text-cyan-400">{{ message.model || 'N/A' }}</span>
                      </div>
                      <div class="text-xs text-zinc-600">{{ formatTime(message) }}</div>
                    </div>
                    <div class="text-sm text-gray-300 whitespace-pre-wrap mb-3">{{ message.content }}</div>
                    <div class="flex items-center gap-2">
                      <button 
                        @click="copyToClipboard(message.content)"
                        class="text-cyan-600/40 hover:text-cyan-500 text-xs"
                      >
                        Copy
                      </button>
                      <button 
                        @click="showRerunModal(message.id, $event)"
                        :disabled="isLoading"
                        class="text-cyan-500 hover:text-cyan-400 text-xs font-medium disabled:opacity-50"
                      >
                        Rerun
                      </button>
                    </div>
                  </div>

                  <!-- Alternatives table -->
                  <div class="bg-zinc-950 border border-zinc-800 rounded p-3">
                    <div class="text-xs text-zinc-600 font-medium mb-3 uppercase">Alternatives</div>
                    <div class="grid grid-cols-3 gap-3">
                      <!-- Original -->
                      <div class="bg-zinc-900 border-2 border-cyan-600/50 rounded p-2">
                        <div class="text-xs text-cyan-500 font-medium mb-1">ORIGINAL</div>
                        <div class="text-xs text-gray-400 line-clamp-3 mb-2">{{ message.content }}</div>
                        <div class="text-xs text-zinc-600 mb-2">{{ message.model }}</div>
                        <button 
                          @click="clearVariants(message.id)"
                          class="w-full px-2 py-1 bg-cyan-600/30 border border-cyan-600/50 text-cyan-400 text-xs rounded hover:bg-cyan-600/40 transition-all"
                        >
                          Keep
                        </button>
                      </div>

                      <!-- Variants -->
                      <div 
                        v-for="(variant, vidx) in getVariants(message.id).filter(v => !(v.provider === message.provider && v.model === message.model)).slice(0, 2)"
                        :key="variant.id"
                        class="bg-zinc-900 border border-zinc-800 rounded p-2 hover:border-cyan-600/30 transition-all"
                      >
                        <div class="text-xs text-zinc-400 font-medium mb-1">ALT {{ vidx + 1 }}</div>
                        <div class="text-xs text-gray-400 line-clamp-3 mb-2">{{ variant.content }}</div>
                        <div class="text-xs text-zinc-600 mb-2">{{ variant.model }}</div>
                        <button 
                          @click="selectVariant(variant.id, message.id)"
                          :disabled="isLoading"
                          class="w-full px-2 py-1 bg-cyan-600/20 border border-cyan-600/30 hover:border-cyan-500 text-cyan-400 text-xs rounded transition-all disabled:opacity-50"
                        >
                          Select
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="isLoading" class="flex justify-start">
            <div class="bg-yellow-600/20 border border-yellow-600/30 rounded px-3 py-2">
              <div class="text-xs text-yellow-500 flex items-center gap-2">
                <div class="w-2 h-2 border border-yellow-500 border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- INPUT -->
      <div class="flex-shrink-0 border-t border-zinc-800 bg-zinc-950 p-3">
        <form @submit.prevent="sendMessage" class="max-w-4xl mx-auto flex gap-2">
          <input
            ref="inputField"
            v-model="inputMessage"
            type="text"
            placeholder="Type your message..."
            class="flex-1 px-3 py-2 bg-zinc-900 border border-zinc-700 hover:border-zinc-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 text-gray-300 text-sm rounded transition-all outline-none"
            :disabled="isLoading || !selectedModel"
          />
          <button
            type="submit"
            :disabled="isLoading || !inputMessage.trim() || !selectedModel"
            class="px-4 py-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:from-zinc-800 disabled:to-zinc-800 text-white font-medium text-sm rounded transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>
    </div>

    <!-- RERUN CONTEXT MENU -->
    <teleport to="body" v-if="rerunModal.show">
      <div class="fixed inset-0 z-40" @click="rerunModal.show = false"></div>
      <div 
        class="fixed bg-zinc-900 border border-zinc-700 rounded shadow-lg w-56 z-50"
        :style="{ top: rerunModal.y + 'px', left: rerunModal.x + 'px' }"
        @click.stop
      >
        <div class="p-2 border-b border-zinc-800">
          <div class="text-xs text-cyan-500 font-medium mb-1">Provider</div>
          <div class="space-y-1 max-h-32 overflow-y-auto">
            <div 
              v-for="provider in getRerunProviders()"
              :key="provider"
              @click="rerunModal.provider = provider; updateRerunModels(messages.find(m => m.id === rerunModal.messageId))"
              :class="[
                'w-full px-2 py-1 text-xs rounded text-left transition-all truncate cursor-pointer',
                rerunModal.provider === provider 
                  ? 'bg-cyan-600/30 text-cyan-400 border border-cyan-600/50' 
                  : 'bg-zinc-800 text-gray-300 hover:bg-zinc-700'
              ]"
            >
              {{ provider.toUpperCase() }}
            </div>
          </div>
        </div>

        <div class="p-2">
          <div class="text-xs text-cyan-500 font-medium mb-1">Model</div>
          <div class="space-y-1 max-h-48 overflow-y-auto">
            <div 
              v-for="model in rerunModal.models"
              :key="model"
              @click="!isLoading && rerunMessage(model)"
              :class="[
                'w-full px-2 py-1 text-xs rounded text-left transition-all truncate',
                isLoading 
                  ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed opacity-50' 
                  : 'bg-zinc-800 text-gray-300 hover:bg-cyan-600/20 hover:text-cyan-400 cursor-pointer'
              ]"
              :title="model"
            >
              {{ model }}
            </div>
          </div>
          <div v-if="isLoading" class="mt-2 pt-2 border-t border-zinc-800">
            <div class="text-xs text-yellow-500 flex items-center gap-2">
              <div class="w-2 h-2 border border-yellow-500 border-t-transparent rounded-full animate-spin"></div>
              Generating...
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { defineOptions } from 'vue'
defineOptions({ name: 'ChatView' })

import { ref, onMounted, nextTick, computed } from 'vue'
import api from './utils/axios'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  provider?: string
  model?: string
  timestamp: number
  is_active?: boolean
}

interface Variant {
  id: string
  original_message_id: string
  content: string
  provider: string
  model: string
  is_canonical: boolean
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const inputField = ref<HTMLInputElement>()
const isLoading = ref(false)
const conversationId = ref<string | null>(null)
const providers = ref<Record<string, {available: boolean, models: string[]}>>({})
const selectedProvider = ref<string>('')
const availableModels = ref<string[]>([])
const selectedModel = ref('')
const messagesContainer = ref<HTMLElement>()
const currentTitle = ref('')
const conversationHistory = ref<{id: string, title: string}[]>([])
const variants = ref<Variant[]>([])

const rerunModal = ref({
  show: false,
  messageId: '',
  provider: '',
  model: '',
  models: [] as string[],
  x: 0,
  y: 0
})

const filteredProviders = computed(() => {
  const filtered: Record<string, any> = {}
  for (const [key, provider] of Object.entries(providers.value)) {
    if (provider.available && provider.models.length > 0) {
      filtered[key] = provider
    }
  }
  return filtered
})

const getVariants = (messageId: string) => variants.value.filter(v => v.original_message_id === messageId)

const getRerunProviders = () => {
  const msg = messages.value.find(m => m.id === rerunModal.value.messageId)
  
  return Object.keys(filteredProviders.value).filter(provider => {
    const allModels = providers.value[provider]?.models || []
    
    if (provider === msg?.provider) {
      return allModels.length > 1
    }
    
    return true
  })
}

const fetchEnabledModels = async () => {
  try {
    const response = await api.get('/api/config/models/enabled')
    const apiProviders = response.data.providers || {}
    const transformed: Record<string, any> = {}
    
    for (const [providerKey, providerData] of Object.entries(apiProviders)) {
      transformed[providerKey] = {
        available: true,
        models: (providerData as any).models || []
      }
    }
    
    providers.value = transformed
    
    if (!selectedProvider.value) {
      const availableProvider = Object.keys(filteredProviders.value)[0]
      if (availableProvider) {
        selectedProvider.value = availableProvider
        onProviderChange()
      }
    }
  } catch (error) {
    console.error('Failed to fetch models:', error)
  }
}

const fetchConversations = async () => {
  try {
    const response = await api.get('/api/chat/conversations')
    conversationHistory.value = response.data.conversations
  } catch (error) {
    console.error('Failed to fetch conversations:', error)
  }
}

const loadConversation = async (convId: string) => {
  try {
    const response = await api.get(`/api/chat/conversations/${convId}/messages`)
    messages.value = response.data.messages.map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      provider: msg.provider,
      model: msg.model,
      timestamp: new Date(msg.timestamp).getTime(),
      is_active: true
    }))
    
    conversationId.value = convId
    if (messages.value.length > 0) {
      const firstUserMsg = messages.value.find(m => m.role === 'user')
      currentTitle.value = firstUserMsg ? firstUserMsg.content.slice(0, 30).toUpperCase() : 'SESSION'
    }
    
    variants.value = []
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to load conversation:', error)
  }
}

const onProviderChange = () => {
  const provider = providers.value[selectedProvider.value]
  if (provider?.available) {
    availableModels.value = provider.models
    selectedModel.value = provider.models[0] || ''
    loadLastUsedModel()
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedModel.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    timestamp: Date.now(),
    is_active: true
  }
  
  messages.value.push(userMessage)
  if (!currentTitle.value) currentTitle.value = inputMessage.value.slice(0, 30).toUpperCase()
  
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
      await fetchConversations()
    }

    messages.value.push({
      id: response.data.message_id,
      role: 'assistant',
      content: response.data.response,
      provider: selectedProvider.value,
      model: selectedModel.value,
      timestamp: Date.now(),
      is_active: true
    })

    if (response.data.variants) {
      variants.value.push(...response.data.variants)
    }

    await nextTick()
    scrollToBottom()
  } catch (error: any) {
    console.error('Failed:', error)
    messages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: `[ERROR] ${error.response?.data?.detail || 'Failed'}`,
      timestamp: Date.now(),
      is_active: true
    })
  } finally {
    isLoading.value = false
    await nextTick()
    inputField.value?.focus()
  }
}

const showRerunModal = (messageId: string, event: MouseEvent) => {
  rerunModal.value.messageId = messageId
  
  const msg = messages.value.find(m => m.id === messageId)
  rerunModal.value.provider = selectedProvider.value
  updateRerunModels(msg)
  
  const rect = (event.target as HTMLElement).getBoundingClientRect()
  rerunModal.value.x = rect.left
  rerunModal.value.y = rect.bottom + 8
  rerunModal.value.show = true
}

const updateRerunModels = (message?: Message) => {
  const provider = rerunModal.value.provider
  const allModels = providers.value[provider]?.models || []
  
  rerunModal.value.models = allModels.filter(model => {
    if (message && message.provider === provider && message.model === model) {
      return false
    }
    return true
  })
  
  rerunModal.value.model = rerunModal.value.models[0] || ''
}

const rerunMessage = async (model: string) => {
  rerunModal.value.show = false
  isLoading.value = true
  
  try {
    const response = await api.post('/api/chat/rerun', {
      original_message_id: rerunModal.value.messageId,
      provider: rerunModal.value.provider,
      model: model
    })

    if (response.data.variant) {
      variants.value.push(response.data.variant)
    }

    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to rerun:', error)
  } finally {
    isLoading.value = false
  }
}

const selectVariant = async (variantId: string, messageId: string) => {
  isLoading.value = true
  
  try {
    const response = await api.post('/api/chat/variants/select', {
      variant_id: variantId,
      original_message_id: messageId
    })

    // Add the new message to the conversation
    if (response.data.new_message) {
      messages.value.push({
        id: response.data.new_message.id,
        role: response.data.new_message.role as 'user' | 'assistant',
        content: response.data.new_message.content,
        provider: response.data.new_message.provider,
        model: response.data.new_message.model,
        timestamp: new Date(response.data.new_message.timestamp).getTime(),
        is_active: true
      })
    }

    // Mark the original message as inactive
    if (response.data.deactivated_message_id) {
      const originalMsg = messages.value.find(m => m.id === response.data.deactivated_message_id)
      if (originalMsg) {
        originalMsg.is_active = false
      }
    }

    // Clear variants for this message
    variants.value = variants.value.filter(v => v.original_message_id !== messageId)
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to select variant:', error)
  } finally {
    isLoading.value = false
  }
}

const clearVariants = (messageId: string) => {
  variants.value = variants.value.filter(v => v.original_message_id !== messageId)
}

const startNewChat = () => {
  messages.value = []
  conversationId.value = null
  inputMessage.value = ''
  currentTitle.value = ''
  variants.value = []
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
  const date = new Date(message.timestamp)
  return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

const LAST_USED_MODEL_KEY = 'juggler_last_used_models'

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

onMounted(async () => {
  await fetchEnabledModels()
  await fetchConversations()
})
</script>

<style scoped>
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
</style>