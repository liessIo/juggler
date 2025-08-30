<template>
  <!-- 
    File: src/components/ProviderSelector.vue
    Provider and model selection component
    Allows switching between AI providers mid-conversation
  -->
  
  <div class="provider-selector">
    <div class="selector-group">
      <!-- Provider Dropdown -->
      <div class="selector-item">
        <label class="selector-label">Provider</label>
        <select 
          v-model="selectedProvider" 
          @change="handleProviderChange"
          :disabled="disabled || providers.length === 0"
          class="selector-dropdown"
        >
          <option value="" disabled>Select Provider</option>
          <option 
            v-for="provider in healthyProviders" 
            :key="provider.id" 
            :value="provider.id"
          >
            {{ provider.name }} ({{ provider.models.length }} models)
          </option>
        </select>
      </div>

      <!-- Model Dropdown -->
      <div class="selector-item" v-if="availableModels.length > 0">
        <label class="selector-label">Model</label>
        <select 
          v-model="selectedModel" 
          @change="handleModelChange"
          :disabled="disabled || availableModels.length === 0"
          class="selector-dropdown"
        >
          <option value="" disabled>Select Model</option>
          <option 
            v-for="model in availableModels" 
            :key="model.id" 
            :value="model.id"
          >
            {{ model.name }}
            <span v-if="model.contextWindow">({{ formatContextWindow(model.contextWindow) }})</span>
          </option>
        </select>
      </div>
    </div>

    <!-- Provider Status Indicators -->
    <div class="provider-status" v-if="providers.length > 0">
      <div 
        v-for="provider in providers" 
        :key="provider.id"
        class="status-indicator"
        :class="[`status-${provider.status}`]"
        :title="`${provider.name}: ${provider.status}${provider.latencyMs ? ` (${provider.latencyMs}ms)` : ''}`"
      >
        <div class="status-dot"></div>
        <span class="status-text">{{ getProviderShortName(provider.name) }}</span>
      </div>
    </div>

    <!-- Switch Button (when changing providers mid-conversation) -->
    <div v-if="showSwitchButton" class="switch-actions">
      <button 
        @click="handleSwitch"
        :disabled="!canSwitch || disabled"
        class="switch-button"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 4l1.41 1.41L6.83 12l6.58 6.59L12 20l-8-8z"/>
          <path d="M12 4l-1.41 1.41L17.17 12l-6.58 6.59L12 20l8-8z"/>
        </svg>
        Switch Provider
      </button>
    </div>

    <!-- No Providers Available -->
    <div v-if="providers.length === 0" class="no-providers">
      <div class="warning-icon">⚠</div>
      <div class="warning-text">
        <div>No AI providers available</div>
        <div class="warning-subtext">Check backend connection</div>
      </div>
    </div>

    <!-- All Providers Down -->
    <div v-else-if="healthyProviders.length === 0" class="no-providers">
      <div class="warning-icon">⚠</div>
      <div class="warning-text">
        <div>All providers are down</div>
        <div class="warning-subtext">{{ downProvidersList }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { AIProvider } from '@/types/chat'

interface Props {
  providers: AIProvider[]
  selectedProvider: string
  selectedModel?: string
  disabled?: boolean
  showSwitchButton?: boolean
}

interface Emits {
  (e: 'providerChange', providerId: string, modelId?: string): void
  (e: 'switchProvider'): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  showSwitchButton: false
})

const emit = defineEmits<Emits>()

// Local reactive state
const selectedProvider = ref(props.selectedProvider)
const selectedModel = ref(props.selectedModel || '')

// Computed properties
const healthyProviders = computed(() => {
  return props.providers.filter(provider => provider.status === 'healthy')
})

const currentProvider = computed(() => {
  return props.providers.find(p => p.id === selectedProvider.value)
})

const availableModels = computed(() => {
  return currentProvider.value?.models || []
})

const canSwitch = computed(() => {
  return selectedProvider.value && 
         selectedProvider.value !== props.selectedProvider &&
         healthyProviders.value.some(p => p.id === selectedProvider.value)
})

const downProvidersList = computed(() => {
  const downProviders = props.providers.filter(p => p.status !== 'healthy')
  return downProviders.map(p => `${p.name}: ${p.status}`).join(', ')
})

// Methods
function handleProviderChange() {
  if (!selectedProvider.value) return
  
  // Auto-select first model when provider changes
  const provider = healthyProviders.value.find(p => p.id === selectedProvider.value)
  if (provider && provider.models.length > 0) {
    selectedModel.value = provider.models[0].id
  } else {
    selectedModel.value = ''
  }
  
  emit('providerChange', selectedProvider.value, selectedModel.value)
}

function handleModelChange() {
  if (selectedProvider.value && selectedModel.value) {
    emit('providerChange', selectedProvider.value, selectedModel.value)
  }
}

function handleSwitch() {
  emit('switchProvider')
}

function formatContextWindow(contextWindow: number): string {
  if (contextWindow >= 1000) {
    return `${(contextWindow / 1000).toFixed(0)}k`
  }
  return contextWindow.toString()
}

function getProviderShortName(name: string): string {
  const shortNames: Record<string, string> = {
    'Ollama': 'OL',
    'Groq': 'GQ', 
    'Gemini': 'GM',
    'OpenAI': 'AI'
  }
  
  // Try exact match first
  if (shortNames[name]) {
    return shortNames[name]
  }
  
  // Fallback to first 2 letters
  return name.substring(0, 2).toUpperCase()
}

// Watchers
watch(() => props.selectedProvider, (newProvider) => {
  selectedProvider.value = newProvider
})

watch(() => props.selectedModel, (newModel) => {
  selectedModel.value = newModel || ''
})

// Auto-select first available provider if none selected
watch(healthyProviders, (providers) => {
  if (!selectedProvider.value && providers.length > 0) {
    selectedProvider.value = providers[0].id
    if (providers[0].models.length > 0) {
      selectedModel.value = providers[0].models[0].id
      emit('providerChange', selectedProvider.value, selectedModel.value)
    }
  }
}, { immediate: true })
</script>

<style scoped>
.provider-selector {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 280px;
}

.selector-group {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.selector-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 120px;
}

.selector-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.selector-dropdown {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
  transition: border-color 0.2s;
}

.selector-dropdown:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.selector-dropdown:disabled {
  background-color: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.provider-status {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: help;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.status-healthy .status-dot {
  background-color: #10b981;
}

.status-degraded .status-dot {
  background-color: #f59e0b;
}

.status-down .status-dot {
  background-color: #ef4444;
}

.status-not_configured .status-dot {
  background-color: #6b7280;
}

.status-healthy .status-text {
  color: #059669;
}

.status-degraded .status-text {
  color: #d97706;
}

.status-down .status-text {
  color: #dc2626;
}

.status-not_configured .status-text {
  color: #6b7280;
}

.switch-actions {
  display: flex;
  justify-content: center;
}

.switch-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.switch-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.no-providers {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #fef3cd;
  border: 1px solid #fbbf24;
  border-radius: 8px;
  color: #92400e;
}

.warning-icon {
  font-size: 1.25rem;
}

.warning-text {
  flex: 1;
}

.warning-subtext {
  font-size: 0.75rem;
  color: #a16207;
  margin-top: 0.125rem;
}

/* Responsive design */
@media (max-width: 640px) {
  .provider-selector {
    min-width: auto;
  }
  
  .selector-group {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .selector-item {
    min-width: auto;
  }
  
  .provider-status {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>