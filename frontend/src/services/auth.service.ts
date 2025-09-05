// frontend/src/services/auth.service.ts
/**
 * Authentication Service for Juggler Frontend
 */

// frontend/src/services/auth.service.ts
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// Type imports
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface DecodedToken {
  sub: string;
  user_id: string;
  scopes: string[];
  exp: number;
  iat: number;
}

interface UserCredentials {
  username: string;
  password: string;
}

interface UserRegistration extends UserCredentials {
  email: string;
}

class AuthService {
  private readonly TOKEN_KEY = 'juggler_access_token';
  private readonly REFRESH_TOKEN_KEY = 'juggler_refresh_token';
  private readonly USER_KEY = 'juggler_user';
  private axiosInstance: AxiosInstance;
  private refreshTokenTimeout?: number;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.axiosInstance = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include token
    this.axiosInstance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor to handle token refresh
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await this.refreshToken();
            const token = this.getToken();
            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.axiosInstance(originalRequest);
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    // Setup auto-refresh
    this.setupTokenRefresh();
  }

  /**
   * Register a new user
   */
  async register(userData: UserRegistration): Promise<TokenResponse> {
    try {
      const response = await this.axiosInstance.post<TokenResponse>(
        '/api/auth/register',
        userData
      );
      
      this.setTokens(response.data);
      this.setupTokenRefresh();
      
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('Registration failed');
    }
  }

  /**
   * Login user
   */
  async login(credentials: UserCredentials): Promise<TokenResponse> {
    try {
      const response = await this.axiosInstance.post<TokenResponse>(
        '/api/auth/login',
        credentials
      );
      
      this.setTokens(response.data);
      this.setupTokenRefresh();
      
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 429) {
        throw new Error('Too many login attempts. Please try again later.');
      }
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('Login failed');
    }
  }

  /**
   * Logout user
   */
  logout(): void {
    this.clearTokens();
    if (this.refreshTokenTimeout) {
      clearTimeout(this.refreshTokenTimeout);
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<void> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await this.axiosInstance.post<TokenResponse>(
        '/api/auth/refresh',
        {},
        {
          headers: {
            'X-Refresh-Token': refreshToken
          }
        }
      );
      
      this.setTokens(response.data);
      this.setupTokenRefresh();
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }

  /**
   * Get current user from token
   */
  getCurrentUser(): DecodedToken | null {
    const token = this.getToken();
    if (!token) return null;

    try {
      const decoded = jwtDecode<DecodedToken>(token);
      
      // Check if token is expired
      if (decoded.exp * 1000 < Date.now()) {
        this.clearTokens();
        return null;
      }
      
      return decoded;
    } catch {
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getCurrentUser();
  }

  /**
   * Check if user has specific scope
   */
  hasScope(scope: string): boolean {
    const user = this.getCurrentUser();
    return user?.scopes?.includes(scope) ?? false;
  }

  /**
   * Setup automatic token refresh
   */
  private setupTokenRefresh(): void {
    if (this.refreshTokenTimeout) {
      clearTimeout(this.refreshTokenTimeout);
    }

    const token = this.getToken();
    if (!token) return;

    try {
      const decoded = jwtDecode<DecodedToken>(token);
      const now = Date.now();
      const expires = decoded.exp * 1000;
      
      // Refresh 1 minute before expiry
      const refreshIn = expires - now - 60000;
      
      if (refreshIn > 0) {
        this.refreshTokenTimeout = setTimeout(() => {
          this.refreshToken().catch(() => {
            this.logout();
            window.location.href = '/login';
          });
        }, refreshIn);
      }
    } catch {
      // Invalid token
      this.clearTokens();
    }
  }

  /**
   * Token storage methods
   */
  private setTokens(response: TokenResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refresh_token);
    
    const decoded = jwtDecode<DecodedToken>(response.access_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(decoded));
  }

  private getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  private clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Get axios instance for API calls
   */
  getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

// Export singleton instance
export default new AuthService();