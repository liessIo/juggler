<!-- frontend/src/ConfigView.vue -->
<template>
  <div class="min-h-screen bg-black text-gray-300 font-mono">
    <!-- Header -->
    <div class="border-b border-cyan-900/30 bg-zinc-950">
      <div class="max-w-6xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="relative">
              <div class="w-8 h-8 border border-cyan-500/50 flex items-center justify-center">
                <div class="w-1 h-4 bg-cyan-500"></div>
                <div class="w-4 h-1 bg-cyan-500 absolute"></div>
              </div>
            </div>
            <div>
              <h1 class="text-gray-100 font-bold text-sm tracking-wider">JUGGLER CONFIGURATION</h1>
              <p class="text-cyan-600 text-xs">SYSTEM SETTINGS</p>
            </div>
          </div>
          <button 
            @click="$router.push('/')"
            class="px-4 py-2 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs tracking-wider transition-all"
          >
            [← BACK TO CHAT]
          </button>
        </div>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-6 py-8">
      <!-- Tabs -->
      <div class="flex gap-1 mb-8 border-b border-cyan-900/30">
        <button 
          @click="activeTab = 'api-keys'"
          :class="[
            'px-4 py-2 text-xs tracking-wider transition-all',
            activeTab === 'api-keys' 
              ? 'bg-zinc-900 border-t border-l border-r border-cyan-500/50 text-cyan-400' 
              : 'border-b border-cyan-900/30 text-gray-500 hover:text-gray-300'
          ]"
        >
          API KEYS
        </button>
        <button 
          @click="activeTab = 'models'"
          :class="[
            'px-4 py-2 text-xs tracking-wider transition-all',
            activeTab === 'models' 
              ? 'bg-zinc-900 border-t border-l border-r border-cyan-500/50 text-cyan-400' 
              : 'border-b border-cyan-900/30 text-gray-500 hover:text-gray-300'
          ]"
        >
          MODEL SELECTION
        </button>
        <button 
          @click="activeTab = 'status'"
          :class="[
            'px-4 py-2 text-xs tracking-wider transition-all',
            activeTab === 'status' 
              ? 'bg-zinc-900 border-t border-l border-r border-cyan-500/50 text-cyan-400' 
              : 'border-b border-cyan-900/30 text-gray-500 hover:text-gray-300'
          ]"
        >
          STATUS
        </button>
      </div>

      <!-- API Keys Tab -->
      <div v-if="activeTab === 'api-keys'" class="space-y-6">
        <div class="text-cyan-600 text-sm mb-4">API KEY CONFIGURATION</div>
        
        <!-- API Key Cards -->
        <div v-for="provider in providers" :key="provider.key" class="bg-zinc-950 border border-cyan-900/30 p-4">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <div :class="['w-2 h-2', getStatusColor(provider.key)]"></div>
              <span class="text-sm text-gray-100">{{ provider.name }}</span>
            </div>
            <span class="text-xs" :class="getStatusTextColor(provider.key)">
              {{ getStatusText(provider.key) }}
            </span>
          </div>
          
          <div class="flex gap-2">
            <input
              v-if="editingKey === provider.key"
              v-model="tempKeys[provider.key]"
              type="password"
              :placeholder="`Enter ${provider.name} API Key`"
              class="flex-1 px-3 py-1.5 bg-black border border-cyan-900/30 text-gray-300 text-xs focus:outline-none focus:border-cyan-500/50"
              @keyup.enter="saveKey(provider.key)"
              @keyup.escape="cancelEdit(provider.key)"
            />
            <input
              v-else
              :value="getMaskedKey(provider.key)"
              readonly
              class="flex-1 px-3 py-1.5 bg-black/50 border border-cyan-900/20 text-gray-500 text-xs"
              :placeholder="config[provider.key]?.exists ? '' : 'No API key configured'"
            />
            
            <button
              v-if="editingKey === provider.key"
              @click="saveKey(provider.key)"
              class="px-3 py-1.5 border border-green-900/30 hover:border-green-500/50 text-green-400 text-xs"
            >
              SAVE
            </button>
            <button
              v-if="editingKey === provider.key"
              @click="cancelEdit(provider.key)"
              class="px-3 py-1.5 border border-gray-900/30 hover:border-gray-500/50 text-gray-400 text-xs"
            >
              CANCEL
            </button>
            <button
              v-if="editingKey !== provider.key"
              @click="startEdit(provider.key)"
              class="px-3 py-1.5 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs"
            >
              {{ config[provider.key]?.exists ? 'EDIT' : 'ADD' }}
            </button>
            <button
              v-if="config[provider.key]?.exists && editingKey !== provider.key"
              @click="deleteKey(provider.key)"
              class="px-3 py-1.5 border border-red-900/30 hover:border-red-500/50 text-red-400 text-xs"
            >
              DELETE
            </button>
          </div>
        </div>
        
        <!-- Status Messages -->
        <div v-if="statusMessage" :class="['text-xs mt-4', statusMessage.type === 'error' ? 'text-red-400' : 'text-green-400']">
          {{ statusMessage.text }}
        </div>
      </div>

      <!-- Model Selection Tab -->
      <div v-if="activeTab === 'models'" class="space-y-6">
        <div class="flex items-center justify-between mb-4">
          <div class="text-cyan-600 text-sm">MODEL SELECTION</div>
          <div class="text-xs text-gray-500">
            Select which models to show in the chat interface
          </div>
        </div>

        <!-- Provider Selector -->
        <div class="flex gap-2 mb-6">
          <button
            v-for="provider in availableProviders"
            :key="provider"
            @click="selectedProvider = provider"
            :class="[
              'px-4 py-2 text-xs border transition-all',
              selectedProvider === provider
                ? 'border-cyan-500/50 bg-zinc-900 text-cyan-400'
                : 'border-cyan-900/30 text-gray-500 hover:text-gray-300'
            ]"
          >
            {{ provider.toUpperCase() }}
            <span v-if="modelCounts[provider]" class="ml-2 text-gray-600">
              ({{ modelCounts[provider].enabled }}/{{ modelCounts[provider].total }})
            </span>
          </button>
        </div>

        <!-- Model List -->
        <div v-if="selectedProvider" class="space-y-4">
          <!-- Actions Bar -->
          <div class="flex items-center justify-between bg-zinc-950 border border-cyan-900/30 p-3">
            <div class="flex gap-2">
              <button
                @click="selectAll"
                class="px-3 py-1 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs"
              >
                SELECT ALL
              </button>
              <button
                @click="selectNone"
                class="px-3 py-1 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs"
              >
                CLEAR ALL
              </button>
            </div>
            <button
              @click="refreshModels"
              :disabled="isRefreshing"
              class="px-3 py-1 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs disabled:opacity-50"
            >
              {{ isRefreshing ? 'REFRESHING...' : 'REFRESH MODELS' }}
            </button>
          </div>

          <!-- Models Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="(modelInfo, modelId) in providerModels[selectedProvider]"
              :key="modelId"
              class="bg-zinc-950 border border-cyan-900/30 p-3 hover:border-cyan-500/30 transition-all"
            >
              <label class="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="modelInfo.enabled"
                  class="mt-1 w-4 h-4 bg-black border border-cyan-500/50 text-cyan-500 focus:ring-0"
                />
                <div class="flex-1">
                  <div class="text-sm text-gray-200">{{ modelInfo.name || modelId }}</div>
                  <div class="text-xs text-gray-500 mt-1">{{ modelInfo.description || 'No description available' }}</div>
                </div>
              </label>
            </div>
          </div>

          <!-- No Models Message -->
          <div v-if="!providerModels[selectedProvider] || Object.keys(providerModels[selectedProvider]).length === 0" 
               class="bg-zinc-950 border border-cyan-900/30 p-8 text-center">
            <div class="text-gray-500 mb-3">No models available for {{ selectedProvider }}</div>
            <button
              @click="refreshModels"
              class="px-4 py-2 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-xs"
            >
              FETCH MODELS
            </button>
          </div>

          <!-- Save Button -->
          <div class="flex justify-end mt-6">
            <button
              @click="saveModelSelection"
              :disabled="isSaving"
              class="px-6 py-2 bg-zinc-900 border border-cyan-500/50 hover:border-cyan-400 text-cyan-400 text-xs tracking-wider disabled:opacity-50"
            >
              {{ isSaving ? 'SAVING...' : 'SAVE SELECTION' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Status Tab -->
      <div v-if="activeTab === 'status'" class="space-y-6">
        <div class="text-cyan-600 text-sm mb-4">SYSTEM STATUS</div>
        
        <!-- Provider Status Cards -->
        <div class="grid grid-cols-3 gap-4">
          <div v-for="(status, provider) in providerStatus" :key="provider" 
               class="bg-zinc-950 border border-cyan-900/30 p-4">
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm text-gray-100">{{ provider.toUpperCase() }}</span>
              <div :class="['w-2 h-2', status.available ? 'bg-green-500' : 'bg-red-500']"></div>
            </div>
            <div class="space-y-1">
              <div class="text-xs text-gray-500">
                Status: <span :class="status.available ? 'text-green-400' : 'text-red-400'">
                  {{ status.available ? 'ONLINE' : 'OFFLINE' }}
                </span>
              </div>
              <div class="text-xs text-gray-500">
                Models: <span class="text-gray-400">{{ status.modelCount || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Tab Management - WICHTIG: activeTab startet mit 'api-keys'
const activeTab = ref('api-keys')

// API Keys Management
const providers = [
  { key: 'groq_api_key', name: 'Groq' },
  { key: 'anthropic_api_key', name: 'Anthropic' },
  { key: 'openai_api_key', name: 'OpenAI' }
]

const config = ref<Record<string, any>>({})
const editingKey = ref<string | null>(null)
const tempKeys = ref<Record<string, string>>({})
const statusMessage = ref<{ type: string; text: string } | null>(null)

// Model Selection
const selectedProvider = ref('ollama')
const availableProviders = ref<string[]>(['ollama', 'groq', 'anthropic'])
const providerModels = ref<Record<string, Record<string, any>>>({})
const isRefreshing = ref(false)
const isSaving = ref(false)

// Provider Status
const providerStatus = ref<Record<string, any>>({})

// Computed
const modelCounts = computed(() => {
  const counts: Record<string, { enabled: number; total: number }> = {}
  
  for (const provider of availableProviders.value) {
    const models = providerModels.value[provider] || {}
    const total = Object.keys(models).length
    const enabled = Object.values(models).filter((m: any) => m.enabled).length
    counts[provider] = { enabled, total }
  }
  
  return counts
})

// API Key Functions
const loadConfig = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/config/`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    config.value = response.data
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

const getMaskedKey = (key: string) => {
  return config.value[key]?.masked || ''
}

const getStatusColor = (key: string) => {
  return config.value[key]?.exists ? 'bg-green-500' : 'bg-gray-700'
}

const getStatusText = (key: string) => {
  return config.value[key]?.exists ? 'CONFIGURED' : 'NOT CONFIGURED'
}

const getStatusTextColor = (key: string) => {
  return config.value[key]?.exists ? 'text-green-500' : 'text-gray-500'
}

const startEdit = (key: string) => {
  editingKey.value = key
  tempKeys.value[key] = ''
}

const cancelEdit = (key: string) => {
  editingKey.value = null
  tempKeys.value[key] = ''
}

const saveKey = async (key: string) => {
  if (!tempKeys.value[key]) {
    cancelEdit(key)
    return
  }
  
  try {
    const update: any = {}
    update[key] = tempKeys.value[key]
    
    await axios.post(`${API_BASE_URL}/api/config/`, update, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    statusMessage.value = { type: 'success', text: 'API key saved successfully' }
    await loadConfig()
    cancelEdit(key)
    
    setTimeout(() => {
      statusMessage.value = null
    }, 3000)
  } catch (error) {
    statusMessage.value = { type: 'error', text: 'Failed to save API key' }
  }
}

const deleteKey = async (key: string) => {
  if (!confirm(`Delete ${key.replace('_api_key', '').toUpperCase()} API key?`)) return
  
  try {
    await axios.delete(`${API_BASE_URL}/api/config/${key}`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    statusMessage.value = { type: 'success', text: 'API key deleted' }
    await loadConfig()
    
    setTimeout(() => {
      statusMessage.value = null
    }, 3000)
  } catch (error) {
    statusMessage.value = { type: 'error', text: 'Failed to delete API key' }
  }
}

// Model Selection Functions
const loadProviderModels = async (provider: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/config/models/${provider}`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    providerModels.value[provider] = response.data.models || {}
  } catch (error) {
    console.error(`Failed to load models for ${provider}:`, error)
    providerModels.value[provider] = {}
  }
}

const refreshModels = async () => {
  if (!selectedProvider.value) return
  
  isRefreshing.value = true
  try {
    await axios.post(
      `${API_BASE_URL}/api/config/models/${selectedProvider.value}/refresh`,
      {},
      { headers: { 'Authorization': `Bearer ${authStore.token}` } }
    )
    
    await loadProviderModels(selectedProvider.value)
  } catch (error) {
    console.error('Failed to refresh models:', error)
  } finally {
    isRefreshing.value = false
  }
}

const selectAll = () => {
  const models = providerModels.value[selectedProvider.value] || {}
  for (const modelId in models) {
    models[modelId].enabled = true
  }
}

const selectNone = () => {
  const models = providerModels.value[selectedProvider.value] || {}
  for (const modelId in models) {
    models[modelId].enabled = false
  }
}

const saveModelSelection = async () => {
  if (!selectedProvider.value) return
  
  isSaving.value = true
  try {
    const models = providerModels.value[selectedProvider.value] || {}
    const enabledModels = Object.keys(models).filter(id => models[id].enabled)
    
    await axios.post(
      `${API_BASE_URL}/api/config/models/${selectedProvider.value}/selection`,
      {
        provider: selectedProvider.value,
        enabled_models: enabledModels
      },
      { headers: { 'Authorization': `Bearer ${authStore.token}` } }
    )
    
    statusMessage.value = { type: 'success', text: 'Model selection saved' }
    setTimeout(() => {
      statusMessage.value = null
    }, 3000)
  } catch (error) {
    console.error('Failed to save model selection:', error)
    statusMessage.value = { type: 'error', text: 'Failed to save model selection' }
  } finally {
    isSaving.value = false
  }
}

const loadProviderStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/providers`)
    const providers = response.data.providers || {}
    
    for (const [name, info] of Object.entries(providers)) {
      providerStatus.value[name] = {
        available: (info as any).available,
        modelCount: (info as any).models?.length || 0
      }
    }
  } catch (error) {
    console.error('Failed to load provider status:', error)
  }
}

// Lifecycle
onMounted(async () => {
  await loadConfig()
  await loadProviderStatus()
  
  // Load models for all providers
  for (const provider of availableProviders.value) {
    await loadProviderModels(provider)
  }
})
</script>

<style scoped>
* {
  font-family: 'Courier New', monospace;
}

input[type="checkbox"] {
  accent-color: #06b6d4;
}
</style>