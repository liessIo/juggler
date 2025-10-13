<!-- frontend/src/App.vue -->
<template>
  <RouterView v-slot="{ Component, route }">
    <KeepAlive :include="['Chat']">
      <component :is="Component" :key="route.meta.keepAlive ? undefined : route.path" />
    </KeepAlive>
  </RouterView>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { KeepAlive } from 'vue'  // ← HIER aus 'vue' importieren
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // Check if user is logged in on app start
  if (authStore.isAuthenticated) {
    authStore.fetchUser()
  }
})
</script>

<style>
/* Global dark theme */
html {
  background: #0a0a0a;
}

body {
  background: #0a0a0a !important;
  margin: 0;
  padding: 0;
  color: #e0e0e0;
  overflow-x: hidden;
}

#app {
  background: #0a0a0a;
  min-height: 100vh;
  width: 100%;
}

* {
  box-sizing: border-box;
}

body {
  background: #0a0a0a !important;
  margin: 0;
  padding: 0;
  color: #e0e0e0;
  overflow-x: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; /* NEU */
}
</style>