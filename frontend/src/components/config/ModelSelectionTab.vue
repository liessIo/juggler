<!-- frontend/src/components/config/ModelSelectionTab.vue -->
<template>
  <div class="config-section">
    <h2>MODEL SELECTION</h2>
    <p class="info-text">Select which models to display in the chat interface</p>
    
    <div v-for="provider in Object.keys(modelSelection)" :key="provider" class="provider-models">
      <div class="provider-models-header">
        <h3>{{ provider.toUpperCase() }}</h3>
        <button @click="refreshModels(provider)" class="btn-refresh">
          ↻ REFRESH
        </button>
      </div>
      
      <div v-if="modelSelection[provider]?.models" class="model-list">
        <div 
          v-for="(model, modelId) in modelSelection[provider].models" 
          :key="modelId"
          class="model-item"
        >
          <label class="checkbox-label">
            <input 
              type="checkbox"
              :checked="model.enabled"
              @change="toggleModel(provider, String(modelId))"
            />
            <span class="model-name">{{ model.name || modelId }}</span>
            <span v-if="model.description" class="model-description">
              {{ model.description }}
            </span>
          </label>
        </div>
      </div>
      
      <div v-else class="no-models">
        <p>No models available. Click REFRESH to load models.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelSelection: any
}>()

const emit = defineEmits<{
  refreshModels: [provider: string]
  toggleModel: [provider: string, modelId: string]
}>()

const refreshModels = (provider: string) => {
  emit('refreshModels', provider)
}

const toggleModel = (provider: string, modelId: string) => {
  emit('toggleModel', provider, modelId)
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

.info-text {
  color: #666;
  margin-bottom: 2rem;
  font-size: 1rem;
  line-height: 1.6;
}

.provider-models {
  background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
}

.provider-models:hover {
  border-color: #00d9ff44;
}

.provider-models-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #2a2a2a;
}

.provider-models-header h3 {
  margin: 0;
  color: #00d9ff;
  font-size: 1.3rem;
  letter-spacing: 2px;
  font-weight: 700;
}

.btn-refresh {
  background: rgba(0, 217, 255, 0.15);
  color: #00d9ff;
  border: 2px solid #00d9ff;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
}

.btn-refresh:hover {
  background: #00d9ff;
  color: #000;
  box-shadow: 0 2px 12px rgba(0, 217, 255, 0.3);
  transform: translateY(-1px);
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-item {
  background: #0a0a0a;
  border: 2px solid #1a1a1a;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  transition: all 0.3s ease;
}

.model-item:hover {
  border-color: #00d9ff44;
  background: #0f0f0f;
  transform: translateX(4px);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #00d9ff;
}

.model-name {
  font-weight: 600;
  color: #fff;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 1rem;
  letter-spacing: 0.5px;
}

.model-description {
  color: #666;
  font-size: 0.9rem;
  margin-left: auto;
  font-style: italic;
}

.no-models {
  text-align: center;
  padding: 3rem;
  color: #555;
  font-size: 1rem;
}
</style>