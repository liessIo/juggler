<!-- frontend/src/views/LoginView.vue -->
<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <h1>Juggler Login</h1>
        
        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        
        <!-- Success Message -->
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>
        
        <!-- Login Form -->
        <form @submit.prevent="handleLogin" v-if="!isLoggedIn">
          <div class="form-group">
            <label for="username">Username</label>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="Enter username"
              required
              :disabled="isLoading"
            />
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              placeholder="Enter password"
              required
              :disabled="isLoading"
            />
          </div>
          
          <button type="submit" :disabled="isLoading" class="btn-login">
            {{ isLoading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
        
        <!-- Logged In Status -->
        <div v-else class="logged-in">
          <p>✅ Logged in as <strong>{{ currentUser }}</strong></p>
          <button @click="goToChat" class="btn-primary">Go to Chat</button>
          <button @click="handleLogout" class="btn-secondary">Logout</button>
        </div>
        
        <!-- Quick Login for Development -->
        <div class="dev-login" v-if="!isLoggedIn">
          <hr />
          <p>Quick Login (Dev):</p>
          <button @click="quickLogin" :disabled="isLoading" class="btn-dev">
            Login as testuser
          </button>
        </div>
        
        <!-- Info Box -->
        <div class="info-box">
          <p><strong>Test Account:</strong></p>
          <p>Username: testuser</p>
          <p>Password: Test123!</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import authService from '@/services/auth.service';

// State
const username = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const isLoggedIn = ref(false);
const currentUser = ref('');

// Check if already logged in
onMounted(() => {
  checkLoginStatus();
});

function checkLoginStatus() {
  const user = authService.getCurrentUser();
  if (user) {
    isLoggedIn.value = true;
    currentUser.value = user.sub || user.username || 'Unknown';
  }
}

async function handleLogin() {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  
  try {
    await authService.login({
      username: username.value,
      password: password.value
    });
    
    successMessage.value = 'Login successful! Redirecting...';
    isLoggedIn.value = true;
    currentUser.value = username.value;
    
    // Redirect after 1 second
    setTimeout(() => {
      window.location.href = '/';
    }, 1000);
    
  } catch (error: any) {
    console.error('Login failed:', error);
    errorMessage.value = error.message || 'Login failed. Please check your credentials.';
  } finally {
    isLoading.value = false;
  }
}

async function quickLogin() {
  username.value = 'testuser';
  password.value = 'Test123!';
  await handleLogin();
}

function handleLogout() {
  authService.logout();
  isLoggedIn.value = false;
  currentUser.value = '';
  successMessage.value = 'Logged out successfully';
  
  // Clear form
  username.value = '';
  password.value = '';
}

function goToChat() {
  window.location.href = '/';
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 1rem;
}

.login-card {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

input:disabled {
  background: #f5f5f5;
}

.btn-login {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-login:hover:not(:disabled) {
  background: #5a67d8;
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: #fee2e2;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.success-message {
  background: #dcfce7;
  color: #16a34a;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.dev-login {
  margin-top: 1rem;
  text-align: center;
}

.dev-login hr {
  border: none;
  border-top: 1px solid #e5e5e5;
  margin: 1rem 0;
}

.dev-login p {
  color: #999;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.btn-dev {
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-dev:hover:not(:disabled) {
  background: #e5e7eb;
}

.info-box {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #6b7280;
}

.info-box p {
  margin: 0.25rem 0;
}

.logged-in {
  text-align: center;
}

.logged-in p {
  margin-bottom: 1rem;
  color: #16a34a;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  margin: 0.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a67d8;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}
</style>