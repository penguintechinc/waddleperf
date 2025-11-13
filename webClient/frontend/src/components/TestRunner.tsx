import { useState, useEffect } from 'react'
import { logout } from '../services/api'
import { websocketService, TestCompleteData, TestProgressData } from '../services/websocket'
import TestForm from './TestForm'
import TestResults from './TestResults'
import RealtimeCharts from './RealtimeCharts'
import './TestRunner.css'

interface User {
  id: number
  username: string
  email: string
  role: string
}

interface TestRunnerProps {
  user: User | null
  onLogout: () => void
  authEnabled: boolean
}

export interface LatencyDataPoint {
  timestamp: number
  latency: number
  index: number
}

function TestRunner({ user, onLogout, authEnabled }: TestRunnerProps) {
  const [isRunningTest, setIsRunningTest] = useState(false)
  const [testProgress, setTestProgress] = useState(0)
  const [testResult, setTestResult] = useState<TestCompleteData | null>(null)
  const [latencyData, setLatencyData] = useState<LatencyDataPoint[]>([])
  const [currentMetrics, setCurrentMetrics] = useState({
    latency: 0,
    throughput: 0,
    jitter: 0,
    packetLoss: 0,
  })
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    console.log('[TestRunner] Initializing WebSocket connection...')
    initializeWebSocket()

    return () => {
      console.log('[TestRunner] Cleaning up WebSocket connection...')
      websocketService.disconnect()
    }
  }, [])

  const initializeWebSocket = async () => {
    try {
      await websocketService.connect()
      setWsConnected(true)

      websocketService.onTestStarted((data) => {
        console.log('[TestRunner] Test started:', data.test_type)
        setIsRunningTest(true)
        setTestProgress(0)
        setTestResult(null)
        setLatencyData([])
        setCurrentMetrics({ latency: 0, throughput: 0, jitter: 0, packetLoss: 0 })
      })

      websocketService.onTestProgress((data: TestProgressData) => {
        console.log('[TestRunner] Test progress:', data.progress.toFixed(1) + '%')
        setTestProgress(data.progress)

        // Simulate latency data points as tests progress
        const simulatedLatency = 10 + Math.random() * 50
        const newDataPoint: LatencyDataPoint = {
          timestamp: Date.now(),
          latency: simulatedLatency,
          index: data.current_index,
        }

        setLatencyData((prev) => [...prev, newDataPoint])
        setCurrentMetrics((prev) => ({
          ...prev,
          latency: simulatedLatency,
        }))
      })

      websocketService.onTestComplete((data: TestCompleteData) => {
        console.log('[TestRunner] Test complete')
        setIsRunningTest(false)
        setTestProgress(100)
        setTestResult(data)

        // Update final metrics
        setCurrentMetrics({
          latency: data.latency_ms || 0,
          throughput: data.throughput_mbps || 0,
          jitter: data.jitter_ms || 0,
          packetLoss: data.packet_loss_percent || 0,
        })
      })

      websocketService.onError((error) => {
        console.error('[TestRunner] WebSocket error:', error)
        setIsRunningTest(false)
      })
    } catch (error) {
      console.error('[TestRunner] Failed to connect WebSocket:', error)
      setWsConnected(false)
    }
  }

  const handleLogout = async () => {
    try {
      console.log('[TestRunner] Logging out...')
      await logout()
      onLogout()
    } catch (error) {
      console.error('[TestRunner] Logout failed:', error)
      onLogout()
    }
  }

  const handleTestStart = (testData: {
    test_type: string
    target: string
    port?: number
    timeout?: number
    count?: number
    protocol_detail?: string
  }) => {
    console.log('[TestRunner] Starting test:', testData)

    if (!wsConnected) {
      console.error('[TestRunner] WebSocket not connected, attempting reconnection...')
      initializeWebSocket()
      return
    }

    const sessionId = sessionStorage.getItem('session_id')
    websocketService.startTest({
      ...testData,
      session_id: sessionId || undefined,
    })
  }

  return (
    <div className="test-runner">
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <h1>WaddlePerf</h1>
            <span className="header-subtitle">Network Performance Testing</span>
          </div>
          <div className="header-right">
            <div className="status-indicators">
              <div className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
                <span className="status-dot"></span>
                {wsConnected ? 'Connected' : 'Disconnected'}
              </div>
            </div>
            {authEnabled && user && (
              <div className="user-menu">
                <span className="user-name">{user.username}</span>
                <button onClick={handleLogout} className="btn-logout">
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          <div className="grid-layout">
            <div className="test-config-section">
              <TestForm onTestStart={handleTestStart} isRunning={isRunningTest} />
            </div>

            <div className="test-monitoring-section">
              {isRunningTest && (
                <div className="progress-section">
                  <h3>Test Progress</h3>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${testProgress}%` }}>
                      <span className="progress-text">{testProgress.toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              )}

              {(isRunningTest || latencyData.length > 0) && (
                <RealtimeCharts
                  latencyData={latencyData}
                  currentMetrics={currentMetrics}
                  isRunning={isRunningTest}
                />
              )}

              {testResult && !isRunningTest && <TestResults result={testResult} />}

              {!isRunningTest && !testResult && latencyData.length === 0 && (
                <div className="welcome-message">
                  <h2>Welcome to WaddlePerf</h2>
                  <p>Configure and run network performance tests using the form on the left.</p>
                  <div className="features-list">
                    <div className="feature-item">
                      <strong>HTTP Testing</strong>
                      <span>Test HTTP/1.1, HTTP/2, and HTTP/3 performance</span>
                    </div>
                    <div className="feature-item">
                      <strong>TCP Testing</strong>
                      <span>Test raw TCP, SSH, and TLS connections</span>
                    </div>
                    <div className="feature-item">
                      <strong>UDP Testing</strong>
                      <span>Test DNS queries and raw UDP performance</span>
                    </div>
                    <div className="feature-item">
                      <strong>ICMP Testing</strong>
                      <span>Test network reachability and latency</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <p>WaddlePerf Web Client v1.0.0 | Network Performance Testing Platform</p>
      </footer>
    </div>
  )
}

export default TestRunner
