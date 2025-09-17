<template>
  <div class="min-h-screen bg-black text-gray-300 font-mono">
    <div class="max-w-4xl mx-auto p-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-cyan-500 mb-2">SYSTEM CONFIGURATION</h1>
        <div class="h-px bg-cyan-900/30"></div>
      </div>

      <!-- API Keys Section -->
      <div class="space-y-6">
        <!-- Groq API Key -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs flex items-center gap-2">
              <span v-if="keyStatus.groq_api_key.exists" class="text-green-500">●</span>
              <span v-else class="text-red-500">●</span>
              <span :class="keyStatus.groq_api_key.exists ? 'text-green-600' : 'text-cyan-600'">
                GROQ API KEY
              </span>
              <span v-if="keyStatus.groq_api_key.exists" class="text-green-500 text-xs">
                [STORED]
              </span>
            </label>
            <button 
              v-if="keyStatus.groq_api_key.exists"
              @click="deleteKey('groq_api_key')"
              class="px-2 py-1 text-xs text-red-400 border border-red-900/30 hover:border-red-500/50 transition-all"
            >
              [DELETE]
            </button>
          </div>
          <div class="relative">
            <input
              v-model="config.groq_api_key"
              type="password"
              :class="[
                'w-full px-3 py-2 bg-zinc-900 text-gray-300 focus:outline-none transition-all',
                keyStatus.groq_api_key.exists ? 'border border-green-900/30 focus:border-green-500/50' : 'border border-cyan-900/30 focus:border-cyan-500/50',
                hasChanges.groq_api_key && 'border-yellow-500/50'
              ]"
              :placeholder="keyStatus.groq_api_key.exists 
                ? 'API key stored. Enter new key to overwrite' 
                : 'No API key stored, please enter Groq key'"
              @input="markChanged('groq_api_key')"
            />
            <div v-if="keyStatus.groq_api_key.exists && keyStatus.groq_api_key.masked" 
                 class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-600">
              {{ keyStatus.groq_api_key.masked }}
            </div>
          </div>
        </div>

        <!-- Anthropic API Key -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs flex items-center gap-2">
              <span v-if="keyStatus.anthropic_api_key.exists" class="text-green-500">●</span>
              <span v-else class="text-red-500">●</span>
              <span :class="keyStatus.anthropic_api_key.exists ? 'text-green-600' : 'text-cyan-600'">
                ANTHROPIC API KEY
              </span>
              <span v-if="keyStatus.anthropic_api_key.exists" class="text-green-500 text-xs">
                [STORED]
              </span>
            </label>
            <button 
              v-if="keyStatus.anthropic_api_key.exists"
              @click="deleteKey('anthropic_api_key')"
              class="px-2 py-1 text-xs text-red-400 border border-red-900/30 hover:border-red-500/50 transition-all"
            >
              [DELETE]
            </button>
          </div>
          <div class="relative">
            <input
              v-model="config.anthropic_api_key"
              type="password"
              :class="[
                'w-full px-3 py-2 bg-zinc-900 text-gray-300 focus:outline-none transition-all',
                keyStatus.anthropic_api_key.exists ? 'border border-green-900/30 focus:border-green-500/50' : 'border border-cyan-900/30 focus:border-cyan-500/50',
                hasChanges.anthropic_api_key && 'border-yellow-500/50'
              ]"
              :placeholder="keyStatus.anthropic_api_key.exists 
                ? 'API key stored. Enter new key to overwrite' 
                : 'No API key stored, please enter Anthropic key'"
              @input="markChanged('anthropic_api_key')"
            />
            <div v-if="keyStatus.anthropic_api_key.exists && keyStatus.anthropic_api_key.masked" 
                 class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-600">
              {{ keyStatus.anthropic_api_key.masked }}
            </div>
          </div>
        </div>

        <!-- OpenAI API Key -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs flex items-center gap-2">
              <span v-if="keyStatus.openai_api_key.exists" class="text-green-500">●</span>
              <span v-else class="text-red-500">●</span>
              <span :class="keyStatus.openai_api_key.exists ? 'text-green-600' : 'text-cyan-600'">
                OPENAI API KEY
              </span>
              <span v-if="keyStatus.openai_api_key.exists" class="text-green-500 text-xs">
                [STORED]
              </span>
            </label>
            <button 
              v-if="keyStatus.openai_api_key.exists"
              @click="deleteKey('openai_api_key')"
              class="px-2 py-1 text-xs text-red-400 border border-red-900/30 hover:border-red-500/50 transition-all"
            >
              [DELETE]
            </button>
          </div>
          <div class="relative">
            <input
              v-model="config.openai_api_key"
              type="password"
              :class="[
                'w-full px-3 py-2 bg-zinc-900 text-gray-300 focus:outline-none transition-all',
                keyStatus.openai_api_key.exists ? 'border border-green-900/30 focus:border-green-500/50' : 'border border-cyan-900/30 focus:border-cyan-500/50',
                hasChanges.openai_api_key && 'border-yellow-500/50'
              ]"
              :placeholder="keyStatus.openai_api_key.exists 
                ? 'API key stored. Enter new key to overwrite' 
                : 'No API key stored, please enter OpenAI key'"
              @input="markChanged('openai_api_key')"
            />
            <div v-if="keyStatus.openai_api_key.exists && keyStatus.openai_api_key.masked" 
                 class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-600">
              {{ keyStatus.openai_api_key.masked }}
            </div>
          </div>
        </div>
      </div>

      <!-- Status Summary -->
      <div class="mt-6 p-4 bg-zinc-900 border border-cyan-900/30">
        <div class="text-xs space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-cyan-600">SYSTEM STATUS:</span>
            <span class="text-green-500">ONLINE</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-cyan-600">CONFIGURED PROVIDERS:</span>
            <span class="text-gray-400">
              {{ Object.values(keyStatus).filter(k => k.exists).length }} / 3
            </span>
          </div>
          <div v-if="Object.values(hasChanges).some(v => v)" class="flex items-center gap-2">
            <span class="text-yellow-500">⚠</span>
            <span class="text-yellow-500">UNSAVED CHANGES</span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="mt-8 flex gap-4">
        <button
          @click="saveConfig"
          :disabled="!Object.values(hasChanges).some(v => v)"
          class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-800 disabled:text-gray-600 text-black font-bold text-sm transition-all"
        >
          [SAVE CONFIG]
        </button>
        <button
          @click="$router.push('/')"
          class="px-4 py-2 border border-cyan-900/30 hover:border-cyan-500/50 text-cyan-400 text-sm transition-all"
        >
          [BACK TO CHAT]
        </button>
      </div>

      <!-- Status Message -->
      <div v-if="statusMessage" class="mt-4 text-sm" :class="statusMessage.type === 'success' ? 'text-green-500' : 'text-red-500'">
        {{ statusMessage.text }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

// Configuration values
const config = ref({
  groq_api_key: '',
  anthropic_api_key: '',
  openai_api_key: ''
})

// Key status from backend
const keyStatus = ref({
  groq_api_key: { exists: false, masked: '' },
  anthropic_api_key: { exists: false, masked: '' },
  openai_api_key: { exists: false, masked: '' }
})

// Track changes
const hasChanges = ref({
  groq_api_key: false,
  anthropic_api_key: false,
  openai_api_key: false
})

const statusMessage = ref<{type: string, text: string} | null>(null)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Load current configuration status
onMounted(async () => {
  await loadConfigStatus()
})

const loadConfigStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/config/`)
    keyStatus.value = response.data
    
    // Reset input fields
    config.value = {
      groq_api_key: '',
      anthropic_api_key: '',
      openai_api_key: ''
    }
    
    // Reset change tracking
    hasChanges.value = {
      groq_api_key: false,
      anthropic_api_key: false,
      openai_api_key: false
    }
  } catch (error) {
    console.error('Failed to load config:', error)
    statusMessage.value = { type: 'error', text: 'Failed to load configuration status' }
  }
}

const markChanged = (key: 'groq_api_key' | 'anthropic_api_key' | 'openai_api_key') => {
  hasChanges.value[key] = true
}

const saveConfig = async () => {
  try {
    // Only send changed values
    const changedConfig: any = {}
    
    Object.keys(config.value).forEach((key) => {
      const k = key as keyof typeof config.value
      if (hasChanges.value[k] && config.value[k]) {
        changedConfig[k] = config.value[k]
      }
    })
    
    if (Object.keys(changedConfig).length === 0) {
      statusMessage.value = { type: 'error', text: 'No changes to save' }
      return
    }
    
    const response = await axios.post(`${API_BASE_URL}/api/config/`, changedConfig)
    statusMessage.value = { type: 'success', text: response.data.message }
    
    // Reload status after save
    setTimeout(async () => {
      await loadConfigStatus()
      statusMessage.value = null
    }, 2000)
  } catch (error) {
    statusMessage.value = { type: 'error', text: 'Failed to save configuration' }
  }
}

const deleteKey = async (key: 'groq_api_key' | 'anthropic_api_key' | 'openai_api_key') => {
  if (!confirm(`Are you sure you want to delete the ${key.replace(/_/g, ' ').toUpperCase()}?`)) {
    return
  }
  
  try {
    // Send DELETE value to backend
    const deleteConfig = { [key]: 'DELETE' }
    await axios.post(`${API_BASE_URL}/api/config/`, deleteConfig)
    
    statusMessage.value = { type: 'success', text: `${key.replace(/_/g, ' ').toUpperCase()} deleted` }
    
    // Reload status
    setTimeout(async () => {
      await loadConfigStatus()
      statusMessage.value = null
    }, 2000)
  } catch (error) {
    statusMessage.value = { type: 'error', text: 'Failed to delete key' }
  }
}
</script>