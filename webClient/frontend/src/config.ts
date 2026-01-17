/**
 * Runtime configuration helper
 * Uses window.__CONFIG__ injected by container entrypoint,
 * falls back to Vite env vars for local development
 */

declare global {
  interface Window {
    __CONFIG__?: {
      API_URL: string;
      WS_URL: string;
      TESTSERVER_URL: string;
    };
  }
}

// Get API URL from runtime config or fall back to Vite env / defaults
export function getApiUrl(): string {
  if (window.__CONFIG__?.API_URL) {
    return window.__CONFIG__.API_URL;
  }
  return import.meta.env.VITE_API_URL || 'http://localhost:5000';
}

// Get WebSocket URL - derived from API URL
export function getWsUrl(): string {
  if (window.__CONFIG__?.WS_URL) {
    return window.__CONFIG__.WS_URL;
  }
  const apiUrl = getApiUrl();
  return apiUrl.replace(/^http/, 'ws');
}

// Get Test Server URL from runtime config or fall back to Vite env / defaults
export function getTestServerUrl(): string {
  if (window.__CONFIG__?.TESTSERVER_URL) {
    return window.__CONFIG__.TESTSERVER_URL;
  }
  return import.meta.env.VITE_TESTSERVER_URL || 'http://localhost:8080';
}

export const config = {
  get apiUrl() {
    return getApiUrl();
  },
  get wsUrl() {
    return getWsUrl();
  },
  get testServerUrl() {
    return getTestServerUrl();
  }
};

export default config;
