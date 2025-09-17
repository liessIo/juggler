<template>
  <div class="min-h-screen bg-black flex items-center justify-center">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-zinc-900 border border-cyan-900/30 mb-4">
          <div class="w-2 h-8 bg-cyan-500"></div>
          <div class="w-8 h-2 bg-cyan-500 absolute"></div>
        </div>
        <h1 class="text-2xl font-mono text-gray-100 tracking-wider">JUGGLER</h1>
        <p class="text-cyan-600 text-xs mt-2">AUTHENTICATION REQUIRED</p>
      </div>

      <!-- Form Container -->
      <div class="bg-zinc-950 border border-cyan-900/30 p-8">
        <!-- Tab Switcher -->
        <div class="flex mb-6">
          <button 
            @click="mode = 'login'"
            :class="[
              'flex-1 py-2 text-xs font-mono tracking-wider border',
              mode === 'login' 
                ? 'bg-zinc-900 border-cyan-500/50 text-cyan-400' 
                : 'bg-black border-cyan-900/30 text-gray-500 hover:text-gray-300'
            ]"
          >
            [LOGIN]
          </button>
          <button 
            @click="mode = 'register'"
            :class="[
              'flex-1 py-2 text-xs font-mono tracking-wider border',
              mode === 'register' 
                ? 'bg-zinc-900 border-cyan-500/50 text-cyan-400' 
                : 'bg-black border-cyan-900/30 text-gray-500 hover:text-gray-300'
            ]"
          >
            [REGISTER]
          </button>
        </div>

        <!-- Login Form -->
        <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-cyan-600 text-xs mb-2">USERNAME</label>
            <input
              v-model="loginForm.username"
              type="text"
              required
              class="w-full px-3 py-2 bg-black border border-cyan-900/30 text-gray-300 text-sm font-mono focus:outline-none focus:border-cyan-500/50"
              placeholder="enter username"
            />
          </div>
          
          <div>
            <label class="block text-cyan-600 text-xs mb-2">PASSWORD</label>
            <input
              v-model="loginForm.password"
              type="password"
              required
              class="w-full px-3 py-2 bg-black border border-cyan-900/30 text-gray-300 text-sm font-mono focus:outline-none focus:border-cyan-500/50"
              placeholder="enter password"
            />
          </div>

          <div v-if="error" class="text-red-500 text-xs">
            ERROR: {{ error }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2 bg-zinc-900 border border-cyan-500/50 text-cyan-400 text-sm font-mono tracking-wider hover:bg-zinc-800 disabled:opacity-50"
          >
            {{ loading ? 'AUTHENTICATING...' : '[CONNECT]' }}
          </button>
        </form>

        <!-- Register Form -->
        <form v-if="mode === 'register'" @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="block text-cyan-600 text-xs mb-2">USERNAME</label>
            <input
              v-model="registerForm.username"
              type="text"
              required
              class="w-full px-3 py-2 bg-black border border-cyan-900/30 text-gray-300 text-sm font-mono focus:outline-none focus:border-cyan-500/50"
              placeholder="choose username"
            />
          </div>

          <div>
            <label class="block text-cyan-600 text-xs mb-2">EMAIL</label>
            <input
              v-model="registerForm.email"
              type="email"
              required
              class="w-full px-3 py-2 bg-black border border-cyan-900/30 text-gray-300 text-sm font-mono focus:outline-none focus:border-cyan-500/50"
              placeholder="enter email"
            />
          </div>
          
          <div>
            <label class="block text-cyan-600 text-xs mb-2">PASSWORD</label>
            <input
              v-model="registerForm.password"
              type="password"
              required
              class="w-full px-3 py-2 bg-black border border-cyan-900/30 text-gray-300 text-sm font-mono focus:outline-none focus:border-cyan-500/50"
              placeholder="create password"
            />
          </div>

          <div v-if="error" class="text-red-500 text-xs">
            ERROR: {{ error }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2 bg-zinc-900 border border-cyan-500/50 text-cyan-400 text-sm font-mono tracking-wider hover:bg-zinc-800 disabled:opacity-50"
          >
            {{ loading ? 'CREATING ACCOUNT...' : '[CREATE]' }}
          </button>
        </form>
      </div>

      <!-- Status -->
      <div class="mt-6 text-center text-xs text-gray-600 font-mono">
        <div>SYSTEM STATUS: <span class="text-green-500">ONLINE</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: ''
})

async function handleLogin() {
  loading.value = true
  error.value = ''
  
  const result = await authStore.login(loginForm.username, loginForm.password)
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }
  
  loading.value = false
}

async function handleRegister() {
  loading.value = true
  error.value = ''
  
  const result = await authStore.register(
    registerForm.username,
    registerForm.email,
    registerForm.password
  )
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }
  
  loading.value = false
}
</script>