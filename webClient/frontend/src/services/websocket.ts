import { io, Socket } from 'socket.io-client'
import { getApiUrl } from '../config'

export interface TestProgressData {
  progress: number
  current_index: number
  total: number
}

export interface TestCompleteData {
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

export interface TestStartData {
  status: string
  test_type: string
}

export interface ErrorData {
  error: string
  status?: number
}

export class WebSocketService {
  private socket: Socket | null = null
  private isConnected = false

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = getApiUrl()
      console.log('[WebSocket] Connecting to:', wsUrl)

      const accessToken = localStorage.getItem('access_token')
      this.socket = io(wsUrl, {
        transports: ['websocket', 'polling'],
        withCredentials: true,
        auth: {
          token: accessToken || undefined
        }
      })

      this.socket.on('connect', () => {
        console.log('[WebSocket] Connected successfully')
        this.isConnected = true
        resolve()
      })

      this.socket.on('connected', (data) => {
        console.log('[WebSocket] Server confirmed connection:', data)
      })

      this.socket.on('connect_error', (error) => {
        console.error('[WebSocket] Connection error:', error)
        this.isConnected = false
        reject(error)
      })

      this.socket.on('disconnect', (reason) => {
        console.log('[WebSocket] Disconnected:', reason)
        this.isConnected = false
      })

      this.socket.on('error', (error: ErrorData) => {
        console.error('[WebSocket] Error:', error)
      })
    })
  }

  disconnect(): void {
    if (this.socket) {
      console.log('[WebSocket] Disconnecting...')
      this.socket.disconnect()
      this.socket = null
      this.isConnected = false
    }
  }

  onTestStarted(callback: (data: TestStartData) => void): void {
    if (this.socket) {
      this.socket.on('test_started', (data: TestStartData) => {
        console.log('[WebSocket] Test started:', data)
        callback(data)
      })
    }
  }

  onTestProgress(callback: (data: TestProgressData) => void): void {
    if (this.socket) {
      this.socket.on('test_progress', (data: TestProgressData) => {
        console.log('[WebSocket] Test progress:', data.progress.toFixed(1) + '%')
        callback(data)
      })
    }
  }

  onTestComplete(callback: (data: TestCompleteData) => void): void {
    if (this.socket) {
      this.socket.on('test_complete', (data: TestCompleteData) => {
        console.log('[WebSocket] Test complete:', data)
        callback(data)
      })
    }
  }

  onError(callback: (error: ErrorData) => void): void {
    if (this.socket) {
      this.socket.on('error', (error: ErrorData) => {
        console.error('[WebSocket] Error event:', error)
        callback(error)
      })
    }
  }

  startTest(testData: {
    test_type: string
    target: string
    port?: number
    timeout?: number
    count?: number
    protocol_detail?: string
    device_serial?: string
    device_hostname?: string
  }): void {
    if (this.socket && this.isConnected) {
      console.log('[WebSocket] Starting test:', testData.test_type, 'to', testData.target)
      this.socket.emit('start_test', testData)
    } else {
      console.error('[WebSocket] Cannot start test - not connected')
    }
  }

  getConnectionStatus(): boolean {
    return this.isConnected
  }
}

export const websocketService = new WebSocketService()
