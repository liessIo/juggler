// frontend/src/services/api-security.service.ts

import authService from '@/services/auth.service';
import DOMPurify from 'dompurify';

interface ValidationResult {
  isValid: boolean;
  error?: string;
}

interface RateLimitEntry {
  timestamps: number[];
}

class APISecurityService {
  private rateLimiters: Map<string, number[]> = new Map();
  
  /**
   * Sanitize user input to prevent XSS
   */
  sanitizeInput(input: string): string {
    // Check if DOMPurify is available
    if (typeof DOMPurify === 'undefined') {
      // Fallback basic sanitization if DOMPurify not loaded
      return input
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
    }
    
    return DOMPurify.sanitize(input, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre'],
      ALLOWED_ATTR: []
    });
  }
  
  /**
   * Validate message content before sending to API
   */
  validateMessage(content: string): ValidationResult {
    // Check if content is empty
    if (!content || content.trim().length === 0) {
      return { 
        isValid: false, 
        error: 'Message cannot be empty' 
      };
    }
    
    // Check length
    if (content.length > 10000) {
      return { 
        isValid: false, 
        error: 'Message must be less than 10,000 characters' 
      };
    }
    
    // Check for potential injection attempts
    const suspiciousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+\s*=/i,
      /import\s+/,
      /require\s*\(/,
      /__proto__/,
      /constructor\s*\(/
    ];
    
    for (const pattern of suspiciousPatterns) {
      if (pattern.test(content)) {
        return { 
          isValid: false, 
          error: 'Message contains potentially harmful content' 
        };
      }
    }
    
    return { isValid: true };
  }
  
  /**
   * Client-side rate limiting
   */
  checkRateLimit(endpoint: string, limit: number = 30, window: number = 60000): boolean {
    const now = Date.now();
    const key = endpoint;
    
    if (!this.rateLimiters.has(key)) {
      this.rateLimiters.set(key, []);
    }
    
    const timestamps = this.rateLimiters.get(key)!;
    
    // Remove old timestamps outside the window
    const cutoff = now - window;
    const validTimestamps = timestamps.filter(t => t > cutoff);
    
    if (validTimestamps.length >= limit) {
      // Update the stored timestamps even if rate limited
      this.rateLimiters.set(key, validTimestamps);
      return false; // Rate limit exceeded
    }
    
    validTimestamps.push(now);
    this.rateLimiters.set(key, validTimestamps);
    
    return true;
  }
  
  /**
   * Reset rate limit for an endpoint
   */
  resetRateLimit(endpoint: string): void {
    this.rateLimiters.delete(endpoint);
  }
  
  /**
   * Get remaining requests for an endpoint
   */
  getRemainingRequests(endpoint: string, limit: number = 30, window: number = 60000): number {
    const now = Date.now();
    const key = endpoint;
    
    if (!this.rateLimiters.has(key)) {
      return limit;
    }
    
    const timestamps = this.rateLimiters.get(key)!;
    const cutoff = now - window;
    const validTimestamps = timestamps.filter(t => t > cutoff);
    
    return Math.max(0, limit - validTimestamps.length);
  }
  
  /**
   * Encrypt sensitive data before storing locally
   * Note: This is a simple XOR encryption for demo - use Web Crypto API in production
   */
  encryptData(data: string, key: string): string {
    if (!data || !key) return '';
    
    try {
      // Simple XOR encryption (not secure for production!)
      const encrypted = btoa(
        data.split('').map((char, i) => 
          String.fromCharCode(char.charCodeAt(0) ^ key.charCodeAt(i % key.length))
        ).join('')
      );
      return encrypted;
    } catch (error) {
      console.error('Encryption failed:', error);
      return '';
    }
  }
  
  /**
   * Decrypt sensitive data
   */
  decryptData(encrypted: string, key: string): string {
    if (!encrypted || !key) return '';
    
    try {
      const data = atob(encrypted);
      const decrypted = data.split('').map((char, i) => 
        String.fromCharCode(char.charCodeAt(0) ^ key.charCodeAt(i % key.length))
      ).join('');
      return decrypted;
    } catch (error) {
      console.error('Decryption failed:', error);
      return '';
    }
  }
  
  /**
   * Secure API key storage in browser
   * IMPORTANT: Never store API keys in frontend in production!
   * This is only for demo/development purposes
   */
  async storeAPIKey(provider: string, apiKey: string): Promise<void> {
    // Get current user for encryption key
    const user = authService.getCurrentUser();
    if (!user) {
      throw new Error('User must be authenticated to store API keys');
    }
    
    const userKey = user.user_id || 'default';
    const encryptionKey = `${provider}_${userKey}`;
    
    // Encrypt the API key
    const encrypted = this.encryptData(apiKey, encryptionKey);
    
    // Store in sessionStorage (more secure than localStorage)
    sessionStorage.setItem(`api_key_${provider}`, encrypted);
    
    // Also send to backend for secure storage
    try {
      await authService.getAxiosInstance().put(`/api/settings/api-keys/${provider}`, {
        api_key: apiKey
      });
    } catch (error) {
      console.error('Failed to store API key on server:', error);
      // Remove from session storage if server storage failed
      sessionStorage.removeItem(`api_key_${provider}`);
      throw error;
    }
  }
  
  /**
   * Retrieve API key
   */
  getAPIKey(provider: string): string | null {
    const encrypted = sessionStorage.getItem(`api_key_${provider}`);
    if (!encrypted) return null;
    
    const user = authService.getCurrentUser();
    if (!user) return null;
    
    const userKey = user.user_id || 'default';
    const encryptionKey = `${provider}_${userKey}`;
    
    try {
      return this.decryptData(encrypted, encryptionKey);
    } catch {
      return null;
    }
  }
  
  /**
   * Remove API key
   */
  removeAPIKey(provider: string): void {
    sessionStorage.removeItem(`api_key_${provider}`);
  }
  
  /**
   * Clear all stored API keys
   */
  clearAllAPIKeys(): void {
    const keysToRemove: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('api_key_')) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => sessionStorage.removeItem(key));
  }
  
  /**
   * Validate API key format for different providers
   */
  validateAPIKeyFormat(provider: string, apiKey: string): boolean {
    const patterns: Record<string, RegExp> = {
      'groq': /^gsk_[a-zA-Z0-9]{32,}$/,
      'gemini': /^AI[a-zA-Z0-9\-_]{35,}$/,
      'openai': /^sk-[a-zA-Z0-9]{48,}$/,
      'anthropic': /^sk-ant-[a-zA-Z0-9]{90,}$/,
      'ollama': /^.+$/ // Ollama doesn't require API keys usually
    };
    
    const pattern = patterns[provider.toLowerCase()];
    if (!pattern) {
      // Unknown provider, allow any non-empty string
      return apiKey.length > 0;
    }
    
    return pattern.test(apiKey);
  }
  
  /**
   * Generate a secure random string (for CSRF tokens, etc.)
   */
  generateSecureRandom(length: number = 32): string {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  
  /**
   * Check if the current environment is secure (HTTPS)
   */
  isSecureContext(): boolean {
    return window.isSecureContext || window.location.protocol === 'https:';
  }
  
  /**
   * Validate URL to prevent SSRF attacks
   */
  isValidUrl(url: string): boolean {
    try {
      const parsed = new URL(url);
      // Only allow HTTP and HTTPS protocols
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return false;
      }
      // Prevent localhost/internal IPs in production
      if (import.meta.env.PROD) {
        const hostname = parsed.hostname.toLowerCase();
        if (
          hostname === 'localhost' ||
          hostname === '127.0.0.1' ||
          hostname.startsWith('192.168.') ||
          hostname.startsWith('10.') ||
          hostname.startsWith('172.')
        ) {
          return false;
        }
      }
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export default new APISecurityService();