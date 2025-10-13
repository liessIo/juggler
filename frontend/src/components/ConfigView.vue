<!-- frontend/src/components/ConfigView.vue -->
<template>
  <div class="config-container">
    <div class="config-header">
      <div class="flex items-center gap-4 mb-4">
        <button 
          @click="$router.push('/')"
          class="back-button"
        >
          ← BACK TO CHAT
        </button>
        <div class="flex-1">
          <h1>SYSTEM CONFIGURATION</h1>
          <p class="subtitle">Configure API keys and provider settings</p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab', { active: activeTab === tab.id }]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <ApiKeysTab
        v-if="activeTab === 'keys'"
        :config="config"
        :api-keys="apiKeys"
        :saving="saving"
        @toggle-provider="toggleProvider"
        @save-config="saveConfig"
        @delete-api-key="deleteApiKey"
      />

      <ModelSelectionTab
        v-if="activeTab === 'models'"
        :model-selection="modelSelection"
        @refresh-models="refreshModels"
        @toggle-model="toggleModel"
      />

      <SystemInfoTab v-if="activeTab === 'system'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import ApiKeysTab from './config/ApiKeysTab.vue'
import ModelSelectionTab from './config/ModelSelectionTab.vue'
import SystemInfoTab from './config/SystemInfoTab.vue'

const authStore = useAuthStore()

const activeTab = ref('keys')
const tabs = [
  { id: 'keys', label: 'API KEYS' },
  { id: 'models', label: 'MODEL SELECTION' },
  { id: 'system', label: 'SYSTEM INFO' }
]

const config = ref({
  groq: { exists: false, active: true, masked: null },
  anthropic: { exists: false, active: true, masked: null },
  openai: { exists: false, active: true, masked: null },
  ollama: { exists: false, active: true, masked: null }
})

const apiKeys = ref({
  groq: '',
  anthropic: '',
  openai: ''
})

const modelSelection = ref<any>({})
const saving = ref(false)

const API_URL = 'http://localhost:8000'

async function loadConfig() {
  try {
    const response = await axios.get(`${API_URL}/api/config/`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    config.value = response.data
  } catch (error) {
    console.error('Error loading config:', error)
  }
}

async function toggleProvider(provider: string) {
  if (config.value[provider as keyof typeof config.value]) {
    config.value[provider as keyof typeof config.value].active = 
      !config.value[provider as keyof typeof config.value].active
    await saveProviderActive(provider)
  }
}

async function saveProviderActive(provider: string) {
  try {
    const providerConfig = config.value[provider as keyof typeof config.value]
    await axios.post(`${API_URL}/api/config/`, {
      [provider]: {
        active: providerConfig.active
      }
    }, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    console.log(`${provider} ${providerConfig.active ? 'activated' : 'deactivated'}`)
  } catch (error) {
    console.error(`Error updating ${provider}:`, error)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const payload: any = {}
    
    if (apiKeys.value.groq) {
      payload.groq = {
        api_key: apiKeys.value.groq,
        active: config.value.groq.active
      }
    }
    if (apiKeys.value.anthropic) {
      payload.anthropic = {
        api_key: apiKeys.value.anthropic,
        active: config.value.anthropic.active
      }
    }
    if (apiKeys.value.openai) {
      payload.openai = {
        api_key: apiKeys.value.openai,
        active: config.value.openai.active
      }
    }
    
    await axios.post(`${API_URL}/api/config/`, payload, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    apiKeys.value = { groq: '', anthropic: '', openai: '' }
    await loadConfig()
    alert('Configuration saved successfully!')
  } catch (error: any) {
    console.error('Error saving config:', error)
    alert('Error saving configuration: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

async function deleteApiKey(provider: string) {
  if (!confirm(`Delete ${provider.toUpperCase()} API key?`)) return
  
  try {
    await axios.post(`${API_URL}/api/config/`, {
      [`DELETE_${provider}_api_key`]: true
    }, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    await loadConfig()
    alert(`${provider.toUpperCase()} API key deleted`)
  } catch (error) {
    console.error('Error deleting API key:', error)
    alert('Error deleting API key')
  }
}

async function loadModelSelection() {
  try {
    const providers = ['ollama', 'groq', 'anthropic']
    
    for (const provider of providers) {
      const response = await axios.get(`${API_URL}/api/config/models/${provider}`, {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      })
      
      if (response.data.models && Object.keys(response.data.models).length > 0) {
        if (!modelSelection.value[provider]) {
          modelSelection.value[provider] = {}
        }
        modelSelection.value[provider].models = response.data.models
      }
    }
  } catch (error) {
    console.error('Error loading model selection:', error)
  }
}

async function refreshModels(provider: string) {
  try {
    await axios.post(`${API_URL}/api/config/models/${provider}/refresh`, {}, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    await loadModelSelection()
  } catch (error) {
    console.error(`Error refreshing ${provider} models:`, error)
    alert(`Error refreshing models: ${error}`)
  }
}

async function toggleModel(provider: string, modelId: string) {
  if (modelSelection.value[provider]?.models[modelId]) {
    modelSelection.value[provider].models[modelId].enabled = 
      !modelSelection.value[provider].models[modelId].enabled
    
    const enabledModels = Object.keys(modelSelection.value[provider].models)
      .filter(id => modelSelection.value[provider].models[id].enabled)
    
    try {
      await axios.post(
        `${API_URL}/api/config/models/${provider}/selection`,
        enabledModels,
        { headers: { 'Authorization': `Bearer ${authStore.token}` } }
      )
    } catch (error) {
      console.error('Error updating model selection:', error)
    }
  }
}

onMounted(() => {
  loadConfig()
  loadModelSelection()
})
</script>

<style scoped>
.config-container {
  min-height: 100vh;
  background: #0a0a0a;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  color: #e0e0e0;
}

.config-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #1a1a1a;
}

.back-button {
  background: rgba(0, 217, 255, 0.15);
  color: #00d9ff;
  border: 2px solid #00d9ff;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
}

.back-button:hover {
  background: #00d9ff;
  color: #000;
  box-shadow: 0 2px 12px rgba(0, 217, 255, 0.3);
  transform: translateY(-1px);
}

.config-header h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #00d9ff;
  margin: 0 0 0.5rem 0;
  letter-spacing: 2px;
  text-shadow: 0 0 15px rgba(0, 217, 255, 0.2);
}

.subtitle {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
  letter-spacing: 0.3px;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2.5rem;
  background: #0f0f0f;
  padding: 0.5rem;
  border-radius: 8px;
  border: 1px solid #1a1a1a;
}

.tab {
  background: transparent;
  border: none;
  color: #666;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 1px;
  border-radius: 6px;
  transition: all 0.3s ease;
  flex: 1;
}

.tab:hover {
  color: #00d9ff;
  background: #1a1a1a;
}

.tab.active {
  color: #000;
  background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.3);
}

.tab-content {
  background: transparent;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.gap-4 {
  gap: 1rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.flex-1 {
  flex: 1;
}
</style>