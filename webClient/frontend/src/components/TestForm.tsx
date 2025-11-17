import { useState, FormEvent } from 'react'
import './TestForm.css'
import {
  validateTarget,
  validateDNSQuery,
  validatePort,
  validateTimeout,
  validateCount,
  validateHTTPProtocol,
  validateTCPProtocol,
  validateUDPProtocol,
  validateICMPProtocol,
  sanitizeString,
  MAX_TARGET_LENGTH,
  MAX_QUERY_LENGTH,
} from '../utils/validation'

interface TestFormProps {
  onTestStart: (testData: {
    test_type: string
    target: string
    port?: number
    timeout?: number
    count?: number
    protocol_detail?: string
    query?: string
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
  const [dnsQuery, setDnsQuery] = useState('google.com') // For UDP DNS queries
  const [validationError, setValidationError] = useState<string>('')

  const protocolOptions: Record<string, string[]> = {
    http: ['HTTP/1.1', 'HTTP/2', 'HTTP/3'],
    tcp: ['Raw TCP', 'SSH', 'TLS'],
    udp: [], // WebClient only supports DNS for UDP
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
    // Set UDP to DNS by default
    if (newType === 'udp') {
      setProtocolDetail('DNS')
      setPort('53')
    } else {
      setProtocolDetail('')
    }
  }


  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setValidationError('')

    // Validate target
    const targetResult = validateTarget(target)
    if (!targetResult.valid) {
      setValidationError(targetResult.error || 'Invalid target')
      return
    }

    // Validate protocol
    let protocolResult
    switch (testType) {
      case 'http':
        protocolResult = validateHTTPProtocol(protocolDetail)
        break
      case 'tcp':
        protocolResult = validateTCPProtocol(protocolDetail)
        break
      case 'udp':
        protocolResult = validateUDPProtocol(protocolDetail || 'DNS')
        break
      case 'icmp':
        protocolResult = validateICMPProtocol(protocolDetail)
        break
    }
    if (protocolResult && !protocolResult.valid) {
      setValidationError(protocolResult.error || 'Invalid protocol')
      return
    }

    // Validate port
    if (port) {
      const portResult = validatePort(port)
      if (!portResult.valid) {
        setValidationError(portResult.error || 'Invalid port')
        return
      }
    }

    // Validate timeout
    const timeoutResult = validateTimeout(timeout)
    if (!timeoutResult.valid) {
      setValidationError(timeoutResult.error || 'Invalid timeout')
      return
    }

    // Validate count
    const countResult = validateCount(count)
    if (!countResult.valid) {
      setValidationError(countResult.error || 'Invalid count')
      return
    }

    // Validate DNS query for UDP
    if (testType === 'udp') {
      const queryResult = validateDNSQuery(dnsQuery)
      if (!queryResult.valid) {
        setValidationError(queryResult.error || 'Invalid DNS query')
        return
      }
    }

    // Sanitize all inputs before sending
    const testData: any = {
      test_type: testType,
      target: sanitizeString(target, MAX_TARGET_LENGTH),
      port: port ? parseInt(port, 10) : undefined,
      timeout: parseInt(timeout, 10),
      count: parseInt(count, 10),
      protocol_detail: protocolDetail ? sanitizeString(protocolDetail, 50) : undefined,
    }

    // For UDP DNS tests, add the query parameter
    if (testType === 'udp' && dnsQuery.trim()) {
      testData.query = sanitizeString(dnsQuery, MAX_QUERY_LENGTH)
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
        {validationError && (
          <div className="error-box" style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'var(--error-bg, #fee)', border: '1px solid var(--error-border, #f88)', borderRadius: '4px', color: 'var(--error-text, #c00)' }}>
            <strong>Validation Error:</strong> {validationError}
          </div>
        )}

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

        {testType === 'udp' ? (
          <>
            <div className="form-group">
              <label htmlFor="target">Target DNS Server</label>
              <input
                type="text"
                id="target"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="8.8.8.8 or dns.google.com"
                required
                disabled={isRunning}
              />
            </div>

            <div className="form-group">
              <label htmlFor="dns-query">DNS Query (hostname to lookup)</label>
              <input
                type="text"
                id="dns-query"
                value={dnsQuery}
                onChange={(e) => setDnsQuery(e.target.value)}
                placeholder="google.com"
                required
                disabled={isRunning}
              />
            </div>

            <div className="form-group">
              <label htmlFor="port">Port</label>
              <input
                type="number"
                id="port"
                value="53"
                onChange={(e) => setPort(e.target.value)}
                min="1"
                max="65535"
                disabled={true}
                readOnly
              />
              <small style={{ color: 'var(--text-secondary)', fontSize: '0.85em', marginTop: '4px', display: 'block' }}>
                DNS uses port 53
              </small>
            </div>
          </>
        ) : (
          <>
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
          </>
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
