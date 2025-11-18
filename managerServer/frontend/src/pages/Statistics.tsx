import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../services/api';
import type { TestResult } from '../types';
import './Statistics.css';

const Statistics: React.FC = () => {
  const [tests, setTests] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deviceFilter, setDeviceFilter] = useState('');
  const [testTypeFilter, setTestTypeFilter] = useState('');
  const [limit, setLimit] = useState(100);

  useEffect(() => {
    loadStatistics();
  }, [limit]);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const data = await api.getRecentTests(limit);
      setTests(data.results);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const filteredTests = tests.filter((test) => {
    const matchesDevice = !deviceFilter || test.device_serial.includes(deviceFilter);
    const matchesType = !testTypeFilter || test.test_type === testTypeFilter;
    return matchesDevice && matchesType;
  });

  const uniqueDevices = Array.from(new Set(tests.map((t) => t.device_serial)));
  const uniqueTestTypes = Array.from(new Set(tests.map((t) => t.test_type)));

  const prepareLatencyChart = () => {
    return filteredTests
      .filter((t) => t.latency != null)
      .slice(0, 50)
      .reverse()
      .map((t, idx) => ({
        index: idx + 1,
        latency: t.latency,
        device: t.device_serial.slice(-6),
        timestamp: new Date(t.created_at).toLocaleTimeString(),
      }));
  };

  const prepareTestTypeChart = () => {
    const typeCounts: Record<string, number> = {};
    filteredTests.forEach((t) => {
      typeCounts[t.test_type] = (typeCounts[t.test_type] || 0) + 1;
    });

    return Object.entries(typeCounts).map(([type, count]) => ({
      type,
      count,
    }));
  };

  const prepareDeviceChart = () => {
    const deviceCounts: Record<string, number> = {};
    filteredTests.forEach((t) => {
      deviceCounts[t.device_serial] = (deviceCounts[t.device_serial] || 0) + 1;
    });

    return Object.entries(deviceCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([device, count]) => ({
        device: device.slice(-8),
        count,
      }));
  };

  const calculateSuccessRate = () => {
    const total = filteredTests.length;
    const successful = filteredTests.filter((t) => t.success !== false).length;
    return total > 0 ? ((successful / total) * 100).toFixed(1) : '0';
  };

  const calculateAvgLatency = () => {
    const latencies = filteredTests.filter((t) => t.latency != null).map((t) => t.latency as number);
    if (latencies.length === 0) return 0;
    const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
    return Math.round(avg * 100) / 100;
  };

  return (
    <div className="statistics-container">
      <h1>Test Statistics</h1>

      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="device-filter">Device Filter:</label>
          <input
            id="device-filter"
            type="text"
            value={deviceFilter}
            onChange={(e) => setDeviceFilter(e.target.value)}
            placeholder="Filter by device serial"
          />
        </div>
        <div className="filter-group">
          <label htmlFor="test-type-filter">Test Type:</label>
          <select id="test-type-filter" value={testTypeFilter} onChange={(e) => setTestTypeFilter(e.target.value)}>
            <option value="">All Types</option>
            {uniqueTestTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="limit-filter">Results Limit:</label>
          <select id="limit-filter" value={limit} onChange={(e) => setLimit(parseInt(e.target.value))}>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="200">200</option>
            <option value="500">500</option>
          </select>
        </div>
        <button className="btn-primary" onClick={loadStatistics}>
          Refresh
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading statistics...</p>
        </div>
      ) : (
        <>
          <div className="stats-summary">
            <div className="summary-card">
              <h3>Total Tests</h3>
              <div className="summary-value">{filteredTests.length}</div>
            </div>
            <div className="summary-card">
              <h3>Success Rate</h3>
              <div className="summary-value">{calculateSuccessRate()}%</div>
            </div>
            <div className="summary-card">
              <h3>Avg Latency</h3>
              <div className="summary-value">{calculateAvgLatency()}ms</div>
            </div>
            <div className="summary-card">
              <h3>Unique Devices</h3>
              <div className="summary-value">{uniqueDevices.length}</div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="chart-card">
              <h2>Latency Over Time</h2>
              {prepareLatencyChart().length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={prepareLatencyChart()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="index" />
                    <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="latency" stroke="#8884d8" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No latency data available</p>
              )}
            </div>

            <div className="chart-card">
              <h2>Tests by Type</h2>
              {prepareTestTypeChart().length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={prepareTestTypeChart()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No test type data available</p>
              )}
            </div>

            <div className="chart-card full-width">
              <h2>Top Devices by Test Count</h2>
              {prepareDeviceChart().length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={prepareDeviceChart()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="device" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#ffc658" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="no-data">No device data available</p>
              )}
            </div>
          </div>

          <div className="table-section">
            <h2>Recent Tests ({filteredTests.length} results)</h2>
            <div className="table-container">
              <table className="stats-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Device</th>
                    <th>Test Type</th>
                    <th>Latency</th>
                    <th>Bandwidth</th>
                    <th>Status</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTests.slice(0, 20).map((test) => (
                    <tr key={test.id}>
                      <td>{test.id}</td>
                      <td>{test.device_serial}</td>
                      <td>{test.test_type}</td>
                      <td>{test.latency != null ? `${test.latency}ms` : 'N/A'}</td>
                      <td>{test.bandwidth != null ? `${test.bandwidth}Mbps` : 'N/A'}</td>
                      <td>
                        <span className={`status-badge ${test.success !== false ? 'success' : 'failure'}`}>
                          {test.success !== false ? 'Success' : 'Failed'}
                        </span>
                      </td>
                      <td>{new Date(test.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Statistics;
