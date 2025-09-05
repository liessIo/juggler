// frontend/src/services/api.ts

import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import authService from '@/services/auth.service';

// Types
export interface Provider {
  name: string;
  available: boolean;
  models: string[];
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  provider?: string;
  model?: string;
  latency?: number;
  tokens?: number;
}

export interface Conversation {
  id: string;
  title?: string;
  messages: Message[];
  created_at: string;
  updated_at?: string;
  provider?: string;
  model?: string;
}

export interface ChatRequest {
  content: string;
  provider: string;
  model?: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  provider: string;
  model?: string;
  timestamp: string;
  latency?: number;
  tokens?: number;
}

export interface ProvidersStatus {
  ollama: Provider;
  groq: Provider;
  gemini: Provider;
  openai?: Provider;
  anthropic?: Provider;
}

// API Error Class
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Main API Class
class JugglerAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    // Create axios instance
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        // Get token from auth service if available
        const token = localStorage.getItem('juggler_access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        console.error('API Response Error:', error.response || error);
        
        // Handle 401 - try to refresh token
        if (error.response?.status === 401) {
          try {
            // Only try to refresh if we have auth service
            if (authService && authService.refreshToken) {
              await authService.refreshToken();
              // Retry original request
              const originalRequest = error.config;
              if (originalRequest) {
                return this.client(originalRequest);
              }
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            console.error('Token refresh failed:', refreshError);
            // Don't redirect if we're already on login page
            if (!window.location.pathname.includes('/login')) {
              window.location.href = '/login';
            }
          }
        }

        // Handle other errors
        const errorData = error.response?.data as any;
const message = String(
  errorData?.detail || 
  errorData?.message || 
  error.message || 
  'An unexpected error occurred'
);

throw new APIError(
  message,
  error.response?.status,
  error.response?.data
);
      }
    );
  }

  // ============== Provider Methods ==============

  /**
   * Get status of all providers
   */
  async getProviders(): Promise<ProvidersStatus> {
    try {
      const response = await this.client.get<ProvidersStatus>('/api/providers/status');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch providers:', error);
      throw new APIError('Could not load AI providers');
    }
  }

  /**
   * Check specific provider availability
   */
  async checkProvider(providerName: string): Promise<boolean> {
    try {
      const providers = await this.getProviders();
      const provider = providers[providerName as keyof ProvidersStatus];
      return provider?.available || false;
    } catch {
      return false;
    }
  }

  // ============== Chat Methods ==============

  /**
   * Send a chat message
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await this.client.post<ChatResponse>('/api/chat/send', request);
      return response.data;
    } catch (error) {
      console.error('Failed to send message:', error);
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError('Failed to send message');
    }
  }

  /**
   * Get all conversations for current user
   */
  async getConversations(): Promise<{ conversations: Conversation[]; total: number }> {
    try {
      const response = await this.client.get('/api/chat/conversations');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      throw new APIError('Could not load conversations');
    }
  }

  /**
   * Get specific conversation
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    try {
      const response = await this.client.get(`/api/chat/conversation/${conversationId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
      throw new APIError('Could not load conversation');
    }
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/chat/conversation/${conversationId}`);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw new APIError('Could not delete conversation');
    }
  }

  // ============== Settings Methods ==============

  /**
   * Update API key for a provider
   */
  async updateAPIKey(provider: string, apiKey: string): Promise<void> {
    try {
      await this.client.put(`/api/settings/api-keys/${provider}`, {
        api_key: apiKey
      });
    } catch (error) {
      console.error('Failed to update API key:', error);
      throw new APIError('Could not update API key');
    }
  }

  /**
   * Get user settings
   */
  async getUserSettings(): Promise<any> {
    try {
      const response = await this.client.get('/api/settings/user');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user settings:', error);
      throw new APIError('Could not load settings');
    }
  }

  /**
   * Update user settings
   */
  async updateUserSettings(settings: any): Promise<void> {
    try {
      await this.client.put('/api/settings/user', settings);
    } catch (error) {
      console.error('Failed to update settings:', error);
      throw new APIError('Could not update settings');
    }
  }

  // ============== Health Check ==============

  /**
   * Check API health
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    try {
      const response = await this.client.get('/api/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new APIError('API is not responding');
    }
  }

  // ============== WebSocket Connection ==============

  /**
   * Create WebSocket connection for real-time chat
   */
  createWebSocket(clientId: string): WebSocket {
    const wsUrl = `ws://localhost:8000/ws/${clientId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return ws;
  }

  // ============== Legacy Support ==============
  // These methods provide backward compatibility with old API structure

  /**
   * Send message (legacy format)
   */
  async chat(
    messages: Message[],
    provider: string,
    model?: string
  ): Promise<{ content: string; latency?: number; tokens?: number }> {
    try {
      // Get the last user message
      const lastMessage = messages[messages.length - 1];
      if (!lastMessage || lastMessage.role !== 'user') {
        throw new Error('No user message found');
      }

      const response = await this.sendMessage({
        content: lastMessage.content,
        provider,
        model
      });

      return {
        content: response.response,
        latency: response.latency,
        tokens: response.tokens
      };
    } catch (error) {
      console.error('Legacy chat failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
const apiInstance = new JugglerAPI();
export default apiInstance;

// Also export the class for testing or multiple instances
export { JugglerAPI };