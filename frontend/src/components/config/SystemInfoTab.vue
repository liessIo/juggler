<!-- frontend/src/components/config/SystemInfoTab.vue -->
<template>
  <div class="config-section">
    <h2>SYSTEM INFORMATION</h2>
    
    <div class="info-grid">
      <div class="info-item">
        <label>Version</label>
        <span>Juggler v2.1.0</span>
      </div>
      <div class="info-item">
        <label>Backend</label>
        <span>FastAPI + SQLAlchemy</span>
      </div>
      <div class="info-item">
        <label>Database</label>
        <span>SQLite</span>
      </div>
      <div class="info-item">
        <label>Frontend</label>
        <span>Vue 3 + TypeScript</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// No props or emits needed - static info only
</script>

<style scoped>
.config-section h2 {
  color: #00d9ff;
  font-size: 1.1rem;
  margin: 0 0 1.25rem 0;
  letter-spacing: 1.5px;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.info-item {
  background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 2rem;
  transition: all 0.3s ease;
}

.info-item:hover {
  border-color: #00d9ff44;
  box-shadow: 0 4px 20px rgba(0, 217, 255, 0.1);
}

.info-item label {
  display: block;
  color: #666;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-weight: 700;
}

.info-item span {
  color: #00d9ff;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}
</style>