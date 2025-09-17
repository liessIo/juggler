<!-- frontend/src/App.vue (NEU - nur Router Container) -->
<template>
  <RouterView />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
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