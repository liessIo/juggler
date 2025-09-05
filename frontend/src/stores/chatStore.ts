// frontend/src/stores/chatStore.ts

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiInstance from '@/services/api';
import type { Provider, Message, Conversation, ChatRequest, ProvidersStatus } from '@/services/api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  provider?: string;
  model?: string;
  latency?: number;
  tokens?: number;
  error?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  provider?: string;
  model?: string;
}

export const useChatStore = defineStore('chat', () => {
  // State
  const sessions = ref<ChatSession[]>([]);
  const currentSessionId = ref<string | null>(null);
  const providers = ref<ProvidersStatus | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const currentProvider = ref<string>('ollama');
  const currentModel = ref<string>('llama3:8b');
  const isInitialized = ref(false);

  // Computed
  const currentSession = computed(() => {
    if (!currentSessionId.value) return null;
    return sessions.value.find(s => s.id === currentSessionId.value) || null;
  });

  const availableProviders = computed(() => {
    if (!providers.value) return [];
    
    const available: Array<{ name: string; models: string[] }> = [];
    
    Object.entries(providers.value).forEach(([name, provider]) => {
      if (provider.available) {
        available.push({
          name,
          models: provider.models
        });
      }
    });
    
    return available;
  });

  const currentMessages = computed(() => {
    return currentSession.value?.messages || [];
  });

  // Actions
  async function initialize() {
    if (isInitialized.value) return;
    
    try {
      isLoading.value = true;
      error.value = null;
      
      // Load providers
      await loadProviders();
      
      // Load saved sessions from localStorage
      loadSessionsFromStorage();
      
      // Create initial session if none exists
      if (sessions.value.length === 0) {
        createNewSession();
      } else {
        currentSessionId.value = sessions.value[0].id;
      }
      
      isInitialized.value = true;
    } catch (err) {
      console.error('Failed to initialize chat store:', err);
      error.value = 'Failed to initialize chat';
    } finally {
      isLoading.value = false;
    }
  }

  async function loadProviders() {
    try {
      const providerData = await apiInstance.getProviders();
      providers.value = providerData;
      
      // Set default provider to first available
      const firstAvailable = availableProviders.value[0];
      if (firstAvailable) {
        currentProvider.value = firstAvailable.name;
        currentModel.value = firstAvailable.models[0] || '';
      }
    } catch (err) {
      console.error('Provider loading error:', err);
      error.value = 'Could not load AI providers';
      
      // Set some defaults even if loading fails
      providers.value = {
        ollama: { name: 'ollama', available: false, models: [] },
        groq: { name: 'groq', available: false, models: [] },
        gemini: { name: 'gemini', available: false, models: [] }
      };
    }
  }

  function createNewSession() {
    const newSession: ChatSession = {
      id: generateId(),
      title: `Chat ${sessions.value.length + 1}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      provider: currentProvider.value,
      model: currentModel.value
    };
    
    sessions.value.unshift(newSession);
    currentSessionId.value = newSession.id;
    saveSessionsToStorage();
    
    return newSession;
  }

  async function sendMessage(content: string) {
    if (!content.trim() || !currentSession.value) return;
    
    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      provider: currentProvider.value,
      model: currentModel.value
    };
    
    currentSession.value.messages.push(userMessage);
    saveSessionsToStorage();
    
    // Send to API
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await apiInstance.sendMessage({
        content: content.trim(),
        provider: currentProvider.value,
        model: currentModel.value,
        conversation_id: currentSession.value.id
      });
      
      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
        provider: response.provider,
        model: response.model,
        latency: response.latency,
        tokens: response.tokens
      };
      
      currentSession.value.messages.push(assistantMessage);
      currentSession.value.updatedAt = new Date();
      
      // Update session title if it's the first exchange
      if (currentSession.value.messages.length === 2) {
        currentSession.value.title = content.slice(0, 50) + (content.length > 50 ? '...' : '');
      }
      
      saveSessionsToStorage();
    } catch (err: any) {
      console.error('Failed to send message:', err);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to get response'}`,
        timestamp: new Date(),
        provider: currentProvider.value,
        model: currentModel.value,
        error: true
      };
      
      currentSession.value.messages.push(errorMessage);
      error.value = err.message || 'Failed to send message';
      saveSessionsToStorage();
    } finally {
      isLoading.value = false;
    }
  }

  function switchProvider(provider: string, model?: string) {
    currentProvider.value = provider;
    
    if (model) {
      currentModel.value = model;
    } else {
      // Set default model for provider
      const providerData = providers.value?.[provider as keyof ProvidersStatus];
      if (providerData && providerData.models.length > 0) {
        currentModel.value = providerData.models[0];
      }
    }
    
    // Update current session if exists
    if (currentSession.value) {
      currentSession.value.provider = provider;
      currentSession.value.model = currentModel.value;
      saveSessionsToStorage();
    }
  }

  function switchSession(sessionId: string) {
    const session = sessions.value.find(s => s.id === sessionId);
    if (session) {
      currentSessionId.value = sessionId;
      // Update provider/model to match session
      if (session.provider) {
        currentProvider.value = session.provider;
      }
      if (session.model) {
        currentModel.value = session.model;
      }
    }
  }

  function deleteSession(sessionId: string) {
    const index = sessions.value.findIndex(s => s.id === sessionId);
    if (index !== -1) {
      sessions.value.splice(index, 1);
      
      // If we deleted the current session, switch to another
      if (currentSessionId.value === sessionId) {
        if (sessions.value.length > 0) {
          currentSessionId.value = sessions.value[0].id;
        } else {
          createNewSession();
        }
      }
      
      saveSessionsToStorage();
    }
  }

  function clearCurrentSession() {
    if (currentSession.value) {
      currentSession.value.messages = [];
      currentSession.value.updatedAt = new Date();
      saveSessionsToStorage();
    }
  }

  function editMessage(messageId: string, newContent: string) {
    if (!currentSession.value) return;
    
    const message = currentSession.value.messages.find(m => m.id === messageId);
    if (message) {
      message.content = newContent;
      currentSession.value.updatedAt = new Date();
      saveSessionsToStorage();
    }
  }

  function deleteMessage(messageId: string) {
    if (!currentSession.value) return;
    
    const index = currentSession.value.messages.findIndex(m => m.id === messageId);
    if (index !== -1) {
      currentSession.value.messages.splice(index, 1);
      currentSession.value.updatedAt = new Date();
      saveSessionsToStorage();
    }
  }

  async function regenerateLastResponse() {
    if (!currentSession.value || currentSession.value.messages.length < 2) return;
    
    // Find last user message
    let lastUserMessageIndex = -1;
    for (let i = currentSession.value.messages.length - 1; i >= 0; i--) {
      if (currentSession.value.messages[i].role === 'user') {
        lastUserMessageIndex = i;
        break;
      }
    }
    
    if (lastUserMessageIndex === -1) return;
    
    // Remove all messages after the last user message
    currentSession.value.messages = currentSession.value.messages.slice(0, lastUserMessageIndex + 1);
    
    // Resend the last user message
    const lastUserMessage = currentSession.value.messages[lastUserMessageIndex];
    await sendMessage(lastUserMessage.content);
  }

  async function refreshProviders() {
    await loadProviders();
  }

  // Storage helpers
  function saveSessionsToStorage() {
    try {
      const dataToSave = {
        sessions: sessions.value.map(s => ({
          ...s,
          messages: s.messages.slice(-100) // Keep only last 100 messages per session
        })),
        currentSessionId: currentSessionId.value,
        currentProvider: currentProvider.value,
        currentModel: currentModel.value
      };
      
      localStorage.setItem('juggler_chat_data', JSON.stringify(dataToSave));
    } catch (err) {
      console.error('Failed to save sessions:', err);
    }
  }

  function loadSessionsFromStorage() {
    try {
      const savedData = localStorage.getItem('juggler_chat_data');
      if (savedData) {
        const parsed = JSON.parse(savedData);
        
        // Convert dates back from strings
        sessions.value = parsed.sessions.map((s: any) => ({
          ...s,
          createdAt: new Date(s.createdAt),
          updatedAt: new Date(s.updatedAt),
          messages: s.messages.map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }))
        }));
        
        if (parsed.currentSessionId) {
          currentSessionId.value = parsed.currentSessionId;
        }
        if (parsed.currentProvider) {
          currentProvider.value = parsed.currentProvider;
        }
        if (parsed.currentModel) {
          currentModel.value = parsed.currentModel;
        }
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
      sessions.value = [];
    }
  }

  function exportSessions() {
    const dataStr = JSON.stringify(sessions.value, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `juggler-chat-export-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }

  function importSessions(jsonData: string) {
    try {
      const imported = JSON.parse(jsonData);
      
      // Validate and convert dates
      const validSessions = imported.map((s: any) => ({
        ...s,
        id: s.id || generateId(),
        createdAt: new Date(s.createdAt || Date.now()),
        updatedAt: new Date(s.updatedAt || Date.now()),
        messages: (s.messages || []).map((m: any) => ({
          ...m,
          id: m.id || generateId(),
          timestamp: new Date(m.timestamp || Date.now())
        }))
      }));
      
      sessions.value = [...sessions.value, ...validSessions];
      saveSessionsToStorage();
    } catch (err) {
      console.error('Failed to import sessions:', err);
      throw new Error('Invalid import file format');
    }
  }

  // Utility
  function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  return {
    // State
    sessions,
    currentSessionId,
    providers,
    isLoading,
    error,
    currentProvider,
    currentModel,
    isInitialized,
    
    // Computed
    currentSession,
    availableProviders,
    currentMessages,
    
    // Actions
    initialize,
    loadProviders,
    createNewSession,
    sendMessage,
    switchProvider,
    switchSession,
    deleteSession,
    clearCurrentSession,
    editMessage,
    deleteMessage,
    regenerateLastResponse,
    refreshProviders,
    exportSessions,
    importSessions
  };
});