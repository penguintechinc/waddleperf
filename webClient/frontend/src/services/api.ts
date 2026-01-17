import axios, { AxiosError } from 'axios'
import { getApiUrl } from '../config'

// API URL from runtime config or Vite env
const API_BASE_URL = getApiUrl()

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth and logging
api.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem('access_token')
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for token refresh and logging
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} from ${response.config.url}`)
    return response
  },
  async (error: AxiosError) => {
    console.error('[API] Response error:', error.response?.status, error.message)

    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && error.config) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          })
          const newAccessToken = response.data.access_token
          localStorage.setItem('access_token', newAccessToken)
          error.config.headers.Authorization = `Bearer ${newAccessToken}`
          return api(error.config)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  success: boolean
  user: {
    id: number
    username: string
    email: string
    role: string
  }
  session_id: string
  access_token: string
  refresh_token: string
}

export interface AuthStatusResponse {
  authenticated: boolean
  auth_enabled: boolean
  user?: {
    id: number
    username: string
    email: string
    role: string
  }
}

export interface TestRequest {
  test_type: string
  target: string
  port?: number
  timeout?: number
  count?: number
  protocol_detail?: string
  device_serial?: string
  device_hostname?: string
}

export interface TestResult {
  test_type: string
  target_host: string
  target_ip: string
  latency_ms?: number
  throughput_mbps?: number
  jitter_ms?: number
  packet_loss_percent?: number
  raw_results?: Record<string, unknown>
  success: boolean
  error?: string
}

export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const response = await api.post<LoginResponse>('/api/v1/auth/login', credentials)
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token)
  }
  if (response.data.refresh_token) {
    localStorage.setItem('refresh_token', response.data.refresh_token)
  }
  return response.data
}

export const logout = async (): Promise<void> => {
  await api.post('/api/v1/auth/logout')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export const checkAuthStatus = async (): Promise<AuthStatusResponse> => {
  const response = await api.get<AuthStatusResponse>('/api/v1/auth/status')
  return response.data
}

export const runTest = async (testRequest: TestRequest): Promise<TestResult> => {
  const response = await api.post<TestResult>('/api/v1/tests/', testRequest)
  return response.data
}

export const checkHealth = async (): Promise<{ status: string; database: string }> => {
  const response = await api.get('/health')
  return response.data
}

export default api
