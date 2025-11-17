import { TestCompleteData } from '../services/websocket'
import './TestResults.css'

interface TestResultsProps {
  result: TestCompleteData
}

function TestResults({ result }: TestResultsProps) {
  const formatValue = (value: number | undefined, unit: string, decimals: number = 2): string => {
    if (value === undefined || value === null) return 'N/A'
    return `${value.toFixed(decimals)} ${unit}`
  }

  const getStatusClass = (success: boolean) => (success ? 'success' : 'error')
  const getStatusText = (success: boolean) => (success ? 'Success' : 'Failed')

  return (
    <div className="test-results">
      <div className="results-header">
        <h3>Test Results</h3>
        <span className={`status-badge ${getStatusClass(result.success)}`}>
          {getStatusText(result.success)}
        </span>
      </div>

      {result.error && (
        <div className="error-box">
          <strong>Error:</strong> {result.error}
        </div>
      )}

      <div className="results-grid">
        <div className="result-card">
          <div className="result-label">Test Type</div>
          <div className="result-value">{result.test_type?.toUpperCase() || 'N/A'}</div>
        </div>

        <div className="result-card">
          <div className="result-label">Target Host</div>
          <div className="result-value">{result.target_host || 'N/A'}</div>
        </div>

        <div className="result-card">
          <div className="result-label">Target IP</div>
          <div className="result-value">{result.target_ip || 'N/A'}</div>
        </div>

        {result.latency_ms !== undefined && result.latency_ms !== null && (
          <div className="result-card highlight">
            <div className="result-label">Latency</div>
            <div className="result-value primary">{formatValue(result.latency_ms, 'ms')}</div>
          </div>
        )}

        {result.throughput_mbps !== undefined && result.throughput_mbps !== null && (
          <div className="result-card highlight">
            <div className="result-label">Throughput</div>
            <div className="result-value primary">{formatValue(result.throughput_mbps, 'Mbps')}</div>
          </div>
        )}

        {result.jitter_ms !== undefined && result.jitter_ms !== null && (
          <div className="result-card highlight">
            <div className="result-label">Jitter</div>
            <div className="result-value primary">{formatValue(result.jitter_ms, 'ms')}</div>
          </div>
        )}

        {result.packet_loss_percent !== undefined && result.packet_loss_percent !== null && (
          <div className="result-card highlight">
            <div className="result-label">Packet Loss</div>
            <div className="result-value primary">
              {formatValue(result.packet_loss_percent, '%')}
            </div>
          </div>
        )}
      </div>

      {result.raw_results && Object.keys(result.raw_results).length > 0 && (
        <div className="raw-results">
          <h4>Detailed Results</h4>
          <pre className="json-output">{JSON.stringify(result.raw_results, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default TestResults
