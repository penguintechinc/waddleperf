import { useState, FormEvent } from 'react'
import './TestForm.css'

interface TestFormProps {
  onTestStart: (testData: {
    test_type: string
    target: string
    port?: number
    timeout?: number
    count?: number
    protocol_detail?: string
  }) => void
  isRunning: boolean
}

function TestForm({ onTestStart, isRunning }: TestFormProps) {
  const [testType, setTestType] = useState('http')
  const [target, setTarget] = useState('')
  const [port, setPort] = useState('')
  const [timeout, setTimeout] = useState('30')
  const [count, setCount] = useState('10')
  const [protocolDetail, setProtocolDetail] = useState('')

  const protocolOptions: Record<string, string[]> = {
    http: ['HTTP/1.1', 'HTTP/2', 'HTTP/3'],
    tcp: ['Raw TCP', 'SSH', 'TLS'],
    udp: ['Raw UDP', 'DNS', 'TLS'],
    icmp: [],
  }

  const defaultPorts: Record<string, string> = {
    http: '443',
    tcp: '22',
    udp: '53',
    icmp: '',
  }

  const handleTestTypeChange = (newType: string) => {
    setTestType(newType)
    setPort(defaultPorts[newType] || '')
    setProtocolDetail('')
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    if (!target.trim()) {
      return
    }

    const testData = {
      test_type: testType,
      target: target.trim(),
      port: port ? parseInt(port, 10) : undefined,
      timeout: parseInt(timeout, 10),
      count: parseInt(count, 10),
      protocol_detail: protocolDetail || undefined,
    }

    console.log('[TestForm] Submitting test:', testData)
    onTestStart(testData)
  }

  return (
    <div className="test-form-container">
      <div className="test-form-header">
        <h2>Test Configuration</h2>
        <p>Configure and run network performance tests</p>
      </div>

      <form onSubmit={handleSubmit} className="test-form">
        <div className="form-group">
          <label htmlFor="test-type">Test Type</label>
          <div className="test-type-buttons">
            {['http', 'tcp', 'udp', 'icmp'].map((type) => (
              <button
                key={type}
                type="button"
                className={`test-type-btn ${testType === type ? 'active' : ''}`}
                onClick={() => handleTestTypeChange(type)}
                disabled={isRunning}
              >
                {type.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {protocolOptions[testType].length > 0 && (
          <div className="form-group">
            <label htmlFor="protocol-detail">Protocol</label>
            <select
              id="protocol-detail"
              value={protocolDetail}
              onChange={(e) => setProtocolDetail(e.target.value)}
              disabled={isRunning}
            >
              <option value="">Auto-detect</option>
              {protocolOptions[testType].map((protocol) => (
                <option key={protocol} value={protocol}>
                  {protocol}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="target">Target Host</label>
          <input
            type="text"
            id="target"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={
              testType === 'http'
                ? 'example.com or https://example.com'
                : testType === 'icmp'
                ? '8.8.8.8 or example.com'
                : 'hostname or IP address'
            }
            required
            disabled={isRunning}
          />
        </div>

        {testType !== 'icmp' && (
          <div className="form-group">
            <label htmlFor="port">Port</label>
            <input
              type="number"
              id="port"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="Auto-detect"
              min="1"
              max="65535"
              disabled={isRunning}
            />
          </div>
        )}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="timeout">Timeout (s)</label>
            <input
              type="number"
              id="timeout"
              value={timeout}
              onChange={(e) => setTimeout(e.target.value)}
              min="1"
              max="300"
              required
              disabled={isRunning}
            />
          </div>

          <div className="form-group">
            <label htmlFor="count">Count</label>
            <input
              type="number"
              id="count"
              value={count}
              onChange={(e) => setCount(e.target.value)}
              min="1"
              max="1000"
              required
              disabled={isRunning}
            />
          </div>
        </div>

        <button type="submit" className="btn-start-test" disabled={isRunning || !target.trim()}>
          {isRunning ? (
            <>
              <span className="spinner-small"></span>
              Running Test...
            </>
          ) : (
            'Start Test'
          )}
        </button>
      </form>

      <div className="test-form-footer">
        <div className="info-item">
          <strong>Timeout:</strong> Maximum time per test attempt
        </div>
        <div className="info-item">
          <strong>Count:</strong> Number of test iterations
        </div>
      </div>
    </div>
  )
}

export default TestForm
