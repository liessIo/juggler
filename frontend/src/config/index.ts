// frontend/src/config/index.ts

interface Config {
  API_URL: string;
  WS_URL: string;
  AUTH_TOKEN_KEY: string;
  REFRESH_TOKEN_KEY: string;
  SESSION_TIMEOUT: number;
  RATE_LIMIT: {
    requests: number;
    window: number;
  };
}

const config: Config = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  AUTH_TOKEN_KEY: 'juggler_access_token',
  REFRESH_TOKEN_KEY: 'juggler_refresh_token',
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  RATE_LIMIT: {
    requests: 30,
    window: 60000 // 1 minute
  }
};

export default config;