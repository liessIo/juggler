<!-- frontend/src/components/config/ProviderCard.vue -->
<template>
  <div class="provider-config">
    <div class="provider-header">
      <div class="provider-title">
        <h3>{{ title }}</h3>
        <span class="provider-status" :class="statusClass">
          {{ statusText }}
        </span>
      </div>
      <div class="toggle-container">
        <span class="toggle-label">{{ isActive ? 'ACTIVE' : 'INACTIVE' }}</span>
        <div 
          class="custom-toggle" 
          :class="{ active: isActive }"
          @click="$emit('toggle')"
        >
          <div class="toggle-slider"></div>
        </div>
      </div>
    </div>
    
    <div class="input-group" v-if="isActive">
      <label>{{ inputLabel }}</label>
      <div class="input-with-action">
        <input 
          :type="inputType"
          :value="modelValue"
          @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
          :placeholder="placeholder"
          :disabled="disabled"
          :class="{ 'readonly-input': readonly }"
        />
        <button 
          v-if="showDelete && exists" 
          @click="$emit('delete')"
          class="btn-delete"
        >
          DELETE
        </button>
      </div>
      <p v-if="helpText" class="help-text">{{ helpText }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  statusText: string
  statusClass: string
  isActive: boolean
  inputLabel: string
  inputType?: string
  modelValue: string
  placeholder: string
  disabled?: boolean
  readonly?: boolean
  showDelete?: boolean
  exists?: boolean
  helpText?: string
}>()

defineEmits<{
  toggle: []
  'update:modelValue': [value: string]
  delete: []
}>()
</script>

<style scoped>
.provider-config {
  background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  transition: all 0.3s ease;
}

.provider-config:hover {
  border-color: #00d9ff44;
  box-shadow: 0 2px 15px rgba(0, 217, 255, 0.08);
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #2a2a2a;
}

.provider-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.provider-title h3 {
  margin: 0;
  font-size: 1rem;
  color: #fff;
  letter-spacing: 1.5px;
  font-weight: 600;
}

.provider-status {
  font-size: 0.65rem;
  padding: 0.3rem 0.75rem;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.provider-status.configured {
  background: rgba(0, 217, 255, 0.15);
  color: #00d9ff;
  border: 1px solid #00d9ff;
  box-shadow: 0 0 10px rgba(0, 217, 255, 0.2);
}

.provider-status.not-configured {
  background: rgba(255, 68, 68, 0.15);
  color: #ff4444;
  border: 1px solid #ff4444;
}

.toggle-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.toggle-label {
  font-size: 0.75rem;
  color: #888;
  font-weight: 600;
  letter-spacing: 1px;
  min-width: 70px;
  text-align: right;
  text-transform: uppercase;
}

.custom-toggle {
  width: 52px;
  height: 26px;
  background: #0a0a0a;
  border: 2px solid #333;
  border-radius: 13px;
  position: relative;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.custom-toggle:hover {
  border-color: #00d9ff88;
}

.custom-toggle.active {
  background: rgba(0, 217, 255, 0.2);
  border-color: #00d9ff;
  box-shadow: 0 0 20px rgba(0, 217, 255, 0.3), inset 0 0 10px rgba(0, 217, 255, 0.1);
}

.toggle-slider {
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #444 0%, #666 100%);
  border-radius: 50%;
  position: absolute;
  top: 1px;
  left: 1px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
}

.custom-toggle.active .toggle-slider {
  left: 27px;
  background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
  box-shadow: 
    0 0 12px rgba(0, 217, 255, 0.5),
    0 2px 4px rgba(0, 0, 0, 0.4);
}

.input-group {
  margin-top: 1.5rem;
}

.input-group label {
  display: block;
  margin-bottom: 0.75rem;
  color: #aaa;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.input-with-action {
  display: flex;
  gap: 0.75rem;
}

input[type="text"],
input[type="password"] {
  flex: 1;
  background: #0a0a0a;
  border: 2px solid #2a2a2a;
  color: #e0e0e0;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  transition: all 0.3s ease;
  letter-spacing: 0.3px;
}

input[type="text"]:focus,
input[type="password"]:focus {
  outline: none;
  border-color: #00d9ff;
  background: #0f0f0f;
  box-shadow: 
    0 0 0 3px rgba(0, 217, 255, 0.1),
    0 0 20px rgba(0, 217, 255, 0.2);
}

input[type="text"]::placeholder,
input[type="password"]::placeholder {
  color: #444;
  font-style: italic;
}

input:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: #050505;
}

.readonly-input {
  opacity: 0.6;
  cursor: default;
}

.help-text {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #555;
  font-style: italic;
  line-height: 1.5;
}

.btn-delete {
  background: rgba(255, 68, 68, 0.15);
  color: #ff4444;
  border: 2px solid #ff4444;
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
}

.btn-delete:hover {
  background: #ff4444;
  color: #000;
  box-shadow: 0 2px 12px rgba(255, 68, 68, 0.3);
  transform: translateY(-1px);
}
</style>