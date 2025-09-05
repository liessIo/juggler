<template>
  <div id="app">
    <LoginView v-if="showLogin" @login-success="handleLoginSuccess" />
    <ChatInterface v-else />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ChatInterface from './components/ChatInterface.vue'
import LoginView from './views/LoginView.vue'
import authService from '@/services/auth.service'

const showLogin = ref(false)

onMounted(() => {
  // Check if user is logged in
  const user = authService.getCurrentUser()
  showLogin.value = !user
})

function handleLoginSuccess() {
  showLogin.value = false
}

// Check for /login in URL
if (window.location.pathname === '/login') {
  showLogin.value = true
}
</script>

<style>
#app {
  height: 100vh;
  margin: 0;
  padding: 0;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>