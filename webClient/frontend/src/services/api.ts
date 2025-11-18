import axios, { AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for logging
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} from ${response.config.url}`)
    return response
  },
  (error: AxiosError) => {
    console.error('[API] Response error:', error.response?.status, error.message)
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
  const response = await api.post<LoginResponse>('/api/auth/login', credentials)
  return response.data
}

export const logout = async (): Promise<void> => {
  await api.post('/api/auth/logout')
}

export const checkAuthStatus = async (): Promise<AuthStatusResponse> => {
  const response = await api.get<AuthStatusResponse>('/api/auth/status')
  return response.data
}

export const runTest = async (testRequest: TestRequest): Promise<TestResult> => {
  const { test_type, ...params } = testRequest
  const response = await api.post<TestResult>(`/api/test/${test_type}`, params)
  return response.data
}

export const checkHealth = async (): Promise<{ status: string; database: string }> => {
  const response = await api.get('/health')
  return response.data
}

export default api
