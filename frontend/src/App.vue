<template>
  <div id="app">
    <ChatInterface />
  </div>
</template>

<script setup lang="ts">
import ChatInterface from './components/ChatInterface.vue'
</script>

<style>
#app {
  height: 100vh;
  margin: 0;
  padding: 0;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>