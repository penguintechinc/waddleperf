import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { LatencyDataPoint } from './TestRunner'
import './RealtimeCharts.css'

interface RealtimeChartsProps {
  latencyData: LatencyDataPoint[]
  currentMetrics: {
    latency: number
    throughput: number
    jitter: number
    packetLoss: number
  }
  isRunning: boolean
}

function RealtimeCharts({ latencyData, currentMetrics, isRunning }: RealtimeChartsProps) {
  const formatLatency = (value: number) => `${value.toFixed(2)}ms`
  const formatThroughput = (value: number) => `${value.toFixed(2)} Mbps`
  const formatPercent = (value: number) => `${value.toFixed(2)}%`

  const getGaugeColor = (value: number, thresholds: number[]) => {
    if (value < thresholds[0]) return '#10b981'
    if (value < thresholds[1]) return '#f59e0b'
    return '#ef4444'
  }

  const getLatencyColor = () => getGaugeColor(currentMetrics.latency, [50, 100])
  const getJitterColor = () => getGaugeColor(currentMetrics.jitter, [10, 30])
  const getPacketLossColor = () => getGaugeColor(currentMetrics.packetLoss, [1, 5])

  return (
    <div className="realtime-charts">
      <div className="charts-header">
        <h3>Real-time Metrics</h3>
        {isRunning && <span className="running-badge">Live</span>}
      </div>

      <div className="gauges-grid">
        <div className="gauge-card">
          <div className="gauge-header">
            <span className="gauge-label">Latency</span>
            <span className="gauge-value" style={{ color: getLatencyColor() }}>
              {formatLatency(currentMetrics.latency)}
            </span>
          </div>
          <div className="gauge-bar">
            <div
              className="gauge-fill"
              style={{
                width: `${Math.min((currentMetrics.latency / 200) * 100, 100)}%`,
                backgroundColor: getLatencyColor(),
              }}
            ></div>
          </div>
          <div className="gauge-footer">
            <span>0ms</span>
            <span>200ms</span>
          </div>
        </div>

        <div className="gauge-card">
          <div className="gauge-header">
            <span className="gauge-label">Throughput</span>
            <span className="gauge-value" style={{ color: '#2563eb' }}>
              {formatThroughput(currentMetrics.throughput)}
            </span>
          </div>
          <div className="gauge-bar">
            <div
              className="gauge-fill"
              style={{
                width: `${Math.min((currentMetrics.throughput / 1000) * 100, 100)}%`,
                backgroundColor: '#2563eb',
              }}
            ></div>
          </div>
          <div className="gauge-footer">
            <span>0</span>
            <span>1000 Mbps</span>
          </div>
        </div>

        <div className="gauge-card">
          <div className="gauge-header">
            <span className="gauge-label">Jitter</span>
            <span className="gauge-value" style={{ color: getJitterColor() }}>
              {formatLatency(currentMetrics.jitter)}
            </span>
          </div>
          <div className="gauge-bar">
            <div
              className="gauge-fill"
              style={{
                width: `${Math.min((currentMetrics.jitter / 50) * 100, 100)}%`,
                backgroundColor: getJitterColor(),
              }}
            ></div>
          </div>
          <div className="gauge-footer">
            <span>0ms</span>
            <span>50ms</span>
          </div>
        </div>

        <div className="gauge-card">
          <div className="gauge-header">
            <span className="gauge-label">Packet Loss</span>
            <span className="gauge-value" style={{ color: getPacketLossColor() }}>
              {formatPercent(currentMetrics.packetLoss)}
            </span>
          </div>
          <div className="gauge-bar">
            <div
              className="gauge-fill"
              style={{
                width: `${Math.min(currentMetrics.packetLoss * 10, 100)}%`,
                backgroundColor: getPacketLossColor(),
              }}
            ></div>
          </div>
          <div className="gauge-footer">
            <span>0%</span>
            <span>10%</span>
          </div>
        </div>
      </div>

      {latencyData.length > 0 && (
        <div className="chart-section">
          <h4>Latency Over Time</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={latencyData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="index"
                label={{ value: 'Test #', position: 'insideBottom', offset: -5 }}
                stroke="#64748b"
              />
              <YAxis
                label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }}
                stroke="#64748b"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                }}
                formatter={(value: number) => [`${value.toFixed(2)} ms`, 'Latency']}
                labelFormatter={(label) => `Test #${label}`}
              />
              <Line
                type="monotone"
                dataKey="latency"
                stroke="#2563eb"
                strokeWidth={2}
                dot={{ fill: '#2563eb', r: 3 }}
                activeDot={{ r: 5 }}
                animationDuration={300}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

export default RealtimeCharts
