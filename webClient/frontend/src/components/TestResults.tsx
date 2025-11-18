import { TestCompleteData } from '../services/websocket'
import './TestResults.css'

interface TestResultsProps {
  result: TestCompleteData
  onClose: () => void
  onRunAgain?: () => void
}

function TestResults({ result, onClose, onRunAgain }: TestResultsProps) {
  const getStatusClass = (success: boolean) => (success ? 'success' : 'error')
  const getStatusText = (success: boolean) => (success ? 'Success' : 'Failed')

  // Get icon based on metric type
  const getMetricIcon = (label: string): string => {
    switch (label.toLowerCase()) {
      case 'latency': return '⚡'
      case 'throughput': return '↕'
      case 'jitter': return '~'
      case 'packet loss': return '📦'
      default: return '•'
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content test-results-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Network Test Results</h2>
            <span className={`status-badge ${getStatusClass(result.success)}`}>
              {getStatusText(result.success)}
            </span>
          </div>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {result.error && (
          <div className="error-box">
            <strong>Error:</strong> {result.error}
          </div>
        )}

        <div className="result-grid">
          <div className="result-card">
            <div className="result-icon info">📡</div>
            <div className="result-value">{result.test_type?.toUpperCase() || 'N/A'}</div>
            <div className="result-label">Test Type</div>
          </div>

          <div className="result-card">
            <div className="result-icon info">🌐</div>
            <div className="result-value" style={{ fontSize: '1.2rem' }}>{result.target_host || 'N/A'}</div>
            <div className="result-label">Target Host</div>
          </div>

          <div className="result-card">
            <div className="result-icon info">🔗</div>
            <div className="result-value" style={{ fontSize: '1.2rem' }}>{result.target_ip || 'N/A'}</div>
            <div className="result-label">Target IP</div>
          </div>

          {result.latency_ms !== undefined && result.latency_ms !== null && (
            <div className="result-card">
              <div className="result-icon latency">{getMetricIcon('latency')}</div>
              <div className="result-value">{result.latency_ms.toFixed(2)}</div>
              <div className="result-unit">ms</div>
              <div className="result-label">Latency</div>
            </div>
          )}

          {result.throughput_mbps !== undefined && result.throughput_mbps !== null && (
            <div className="result-card">
              <div className="result-icon download">{getMetricIcon('throughput')}</div>
              <div className="result-value">{result.throughput_mbps.toFixed(2)}</div>
              <div className="result-unit">Mbps</div>
              <div className="result-label">Throughput</div>
            </div>
          )}

          {result.jitter_ms !== undefined && result.jitter_ms !== null && (
            <div className="result-card">
              <div className="result-icon jitter">{getMetricIcon('jitter')}</div>
              <div className="result-value">{result.jitter_ms.toFixed(2)}</div>
              <div className="result-unit">ms</div>
              <div className="result-label">Jitter</div>
            </div>
          )}

          {result.packet_loss_percent !== undefined && result.packet_loss_percent !== null && (
            <div className="result-card">
              <div className="result-icon upload">{getMetricIcon('packet loss')}</div>
              <div className="result-value">{result.packet_loss_percent.toFixed(1)}</div>
              <div className="result-unit">%</div>
              <div className="result-label">Packet Loss</div>
            </div>
          )}
        </div>

        {result.raw_results && Object.keys(result.raw_results).length > 0 && (
          <div className="raw-results">
            <h4>Detailed Results</h4>
            <pre className="json-output">{JSON.stringify(result.raw_results, null, 2)}</pre>
          </div>
        )}

        <div className="modal-actions">
          <button onClick={onClose} className="btn-close-modal">
            Close
          </button>
          {onRunAgain && (
            <button onClick={() => { onClose(); onRunAgain(); }} className="btn-restart-speedtest">
              Run Again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default TestResults
