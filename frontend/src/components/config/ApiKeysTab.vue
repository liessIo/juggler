<!-- frontend/src/components/config/ApiKeysTab.vue -->
<template>
  <div class="config-section">
    <h2>PROVIDER API KEYS</h2>
    
    <!-- Groq -->
    <ProviderCard
      title="GROQ"
      :status-text="config.groq?.exists ? 'CONFIGURED' : 'NOT CONFIGURED'"
      :status-class="config.groq?.exists ? 'configured' : 'not-configured'"
      :is-active="config.groq?.active ?? true"
      input-label="API Key"
      input-type="password"
      v-model="apiKeys.groq"
      :placeholder="config.groq?.masked || 'Enter Groq API key'"
      :disabled="!config.groq?.active"
      show-delete
      :exists="config.groq?.exists"
      @toggle="toggleProvider('groq')"
      @delete="deleteApiKey('groq')"
    />

    <!-- Anthropic -->
    <ProviderCard
      title="ANTHROPIC (Claude)"
      :status-text="config.anthropic?.exists ? 'CONFIGURED' : 'NOT CONFIGURED'"
      :status-class="config.anthropic?.exists ? 'configured' : 'not-configured'"
      :is-active="config.anthropic?.active ?? true"
      input-label="API Key"
      input-type="password"
      v-model="apiKeys.anthropic"
      :placeholder="config.anthropic?.masked || 'Enter Anthropic API key'"
      :disabled="!config.anthropic?.active"
      show-delete
      :exists="config.anthropic?.exists"
      @toggle="toggleProvider('anthropic')"
      @delete="deleteApiKey('anthropic')"
    />

    <!-- OpenAI -->
    <ProviderCard
      title="OPENAI"
      :status-text="config.openai?.exists ? 'CONFIGURED' : 'NOT CONFIGURED'"
      :status-class="config.openai?.exists ? 'configured' : 'not-configured'"
      :is-active="config.openai?.active ?? true"
      input-label="API Key"
      input-type="password"
      v-model="apiKeys.openai"
      :placeholder="config.openai?.masked || 'Enter OpenAI API key'"
      :disabled="!config.openai?.active"
      show-delete
      :exists="config.openai?.exists"
      @toggle="toggleProvider('openai')"
      @delete="deleteApiKey('openai')"
    />

    <!-- Ollama -->
    <ProviderCard
      title="OLLAMA (Local)"
      status-text="LOCAL"
      status-class="configured"
      :is-active="config.ollama?.active ?? true"
      input-label="Base URL"
      input-type="text"
      model-value="http://localhost:11434"
      placeholder=""
      disabled
      readonly
      help-text="Ollama runs locally and doesn't require an API key"
      @toggle="toggleProvider('ollama')"
    />

    <!-- Save Button -->
    <div class="actions">
      <button @click="saveConfig" class="btn-primary" :disabled="saving">
        {{ saving ? 'SAVING...' : 'SAVE CONFIGURATION' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ProviderCard from './ProviderCard.vue'

const props = defineProps<{
  config: any
  apiKeys: any
  saving: boolean
}>()

const emit = defineEmits<{
  toggleProvider: [provider: string]
  saveConfig: []
  deleteApiKey: [provider: string]
}>()

const toggleProvider = (provider: string) => {
  emit('toggleProvider', provider)
}

const saveConfig = () => {
  emit('saveConfig')
}

const deleteApiKey = (provider: string) => {
  emit('deleteApiKey', provider)
}
</script>

<style scoped>
.config-section h2 {
  color: #00d9ff;
  font-size: 1.1rem;
  margin: 0 0 1.25rem 0;
  letter-spacing: 1.5px;
  font-weight: 600;
}

.actions {
  margin-top: 2.5rem;
  display: flex;
  justify-content: flex-end;
  padding-top: 2rem;
  border-top: 1px solid #1a1a1a;
}

.btn-primary {
  background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
  color: #000;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 1.5px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  box-shadow: 0 2px 10px rgba(0, 217, 255, 0.25);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 217, 255, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
</style>