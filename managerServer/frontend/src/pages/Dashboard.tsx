import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import type { TestResult } from '../types';
import './Dashboard.css';

interface StatCard {
  title: string;
  value: string | number;
  subtitle?: string;
}

const Dashboard: React.FC = () => {
  const [recentTests, setRecentTests] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    totalTests: 0,
    successRate: 0,
    avgLatency: 0,
    uniqueDevices: 0,
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const data = await api.getRecentTests(50);
      setRecentTests(data.results);
      calculateStats(data.results);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (tests: TestResult[]) => {
    const totalTests = tests.length;
    const successfulTests = tests.filter((t) => t.success !== false).length;
    const successRate = totalTests > 0 ? (successfulTests / totalTests) * 100 : 0;

    const latencies = tests.filter((t) => t.latency != null).map((t) => t.latency as number);
    const avgLatency = latencies.length > 0 ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0;

    const uniqueDevices = new Set(tests.map((t) => t.device_serial)).size;

    setStats({
      totalTests,
      successRate: Math.round(successRate),
      avgLatency: Math.round(avgLatency * 100) / 100,
      uniqueDevices,
    });
  };

  const prepareChartData = () => {
    return recentTests
      .filter((t) => t.latency != null)
      .slice(0, 20)
      .reverse()
      .map((t, index) => ({
        name: `Test ${index + 1}`,
        latency: t.latency,
        timestamp: new Date(t.created_at).toLocaleTimeString(),
      }));
  };

  const statCards: StatCard[] = [
    { title: 'Total Tests', value: stats.totalTests, subtitle: 'Recent tests' },
    { title: 'Success Rate', value: `${stats.successRate}%`, subtitle: 'Last 50 tests' },
    { title: 'Avg Latency', value: `${stats.avgLatency}ms`, subtitle: 'Network performance' },
    { title: 'Active Devices', value: stats.uniqueDevices, subtitle: 'Unique devices' },
  ];

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <h1>Dashboard</h1>
      {error && <div className="error-message">{error}</div>}

      <div className="stats-grid">
        {statCards.map((card, index) => (
          <div key={index} className="stat-card">
            <h3>{card.title}</h3>
            <div className="stat-value">{card.value}</div>
            {card.subtitle && <div className="stat-subtitle">{card.subtitle}</div>}
          </div>
        ))}
      </div>

      <div className="chart-section">
        <h2>Recent Test Latency</h2>
        {prepareChartData().length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={prepareChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency" stroke="#8884d8" activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No latency data available</p>
        )}
      </div>

      <div className="recent-tests-section">
        <h2>Recent Tests</h2>
        <div className="tests-table-container">
          <table className="tests-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Test Type</th>
                <th>Latency</th>
                <th>Status</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {recentTests.slice(0, 10).map((test) => (
                <tr key={test.id}>
                  <td>{test.device_serial}</td>
                  <td>{test.test_type}</td>
                  <td>{test.latency != null ? `${test.latency}ms` : 'N/A'}</td>
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
    </div>
  );
};

export default Dashboard;
