// frontend/src/main.ts
import { createApp } from 'vue';
import { createPinia } from 'pinia';
// import router from './router';
import App from './App.vue';
import authService from '@/services/auth.service';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
// app.use(router);

// Check authentication on app start
authService.getCurrentUser();

app.mount('#app');