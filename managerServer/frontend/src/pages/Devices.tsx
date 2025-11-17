import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface Device {
  id: number;
  device_serial: string;
  device_hostname: string;
  device_os: string;
  device_os_version: string;
  client_type: string;
  client_version: string | null;
  enrolled_at: string;
  last_seen: string | null;
  is_active: boolean;
  ou_id: number;
  ou_name: string;
  minutes_since_last_seen: number | null;
  status: 'never' | 'online' | 'recent' | 'offline' | 'stale';
}

interface DeviceStats {
  total: number;
  online: number;
  recent: number;
  offline: number;
  stale: number;
  active: number;
  inactive: number;
}

const Devices: React.FC = () => {
  const { user } = useAuth();
  const [devices, setDevices] = useState<Device[]>([]);
  const [stats, setStats] = useState<DeviceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState('');

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  useEffect(() => {
    fetchDevices();
    fetchStats();
  }, [page, statusFilter, searchTerm]);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const params: any = { page, per_page: 25 };

      if (searchTerm) params.search = searchTerm;
      if (statusFilter !== 'all') params.status = statusFilter;

      const response = await axios.get(`${API_URL}/api/v1/devices`, {
        params,
        withCredentials: true,
      });

      setDevices(response.data.devices);
      setTotalPages(response.data.pages);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch devices');
      console.error('Error fetching devices:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/devices/stats`, {
        withCredentials: true,
      });
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching device stats:', err);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      online: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      recent: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      offline: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      stale: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      never: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };

    return badges[status] || badges.never;
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      online: 'Online',
      recent: 'Recent',
      offline: 'Offline',
      stale: 'Stale',
      never: 'Never',
    };

    return texts[status] || 'Unknown';
  };

  const formatLastSeen = (lastSeen: string | null, minutesSince: number | null) => {
    if (!lastSeen) return 'Never';

    if (minutesSince === null) return 'Unknown';

    if (minutesSince < 1) return 'Just now';
    if (minutesSince < 60) return `${minutesSince}m ago`;

    const hours = Math.floor(minutesSince / 60);
    if (hours < 24) return `${hours}h ago`;

    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const handleDeactivate = async (deviceId: number) => {
    if (!confirm('Are you sure you want to deactivate this device?')) return;

    try {
      await axios.post(
        `${API_URL}/api/v1/devices/${deviceId}/deactivate`,
        {},
        { withCredentials: true }
      );
      fetchDevices();
      fetchStats();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to deactivate device');
    }
  };

  const handleReactivate = async (deviceId: number) => {
    try {
      await axios.post(
        `${API_URL}/api/v1/devices/${deviceId}/reactivate`,
        {},
        { withCredentials: true }
      );
      fetchDevices();
      fetchStats();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to reactivate device');
    }
  };

  const canManageDevices = user?.role === 'global_admin' || user?.role === 'ou_admin';

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Devices</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Monitor enrolled devices and their check-in status
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg">
          {error}
        </div>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Devices</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400">Online Now</div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.online}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400">Recently Seen</div>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.recent}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600 dark:text-gray-400">Offline/Stale</div>
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {stats.offline + stats.stale}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Search
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              placeholder="Search by serial or hostname..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Status Filter
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">All Devices</option>
              <option value="online">Online Only</option>
              <option value="offline">Offline Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Devices Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading...</div>
        ) : devices.length === 0 ? (
          <div className="p-8 text-center text-gray-600 dark:text-gray-400">
            No devices found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Device
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Organization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Last Seen
                  </th>
                  {canManageDevices && (
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {devices.map((device) => (
                  <tr key={device.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {device.device_hostname}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {device.device_serial}
                      </div>
                      <div className="text-xs text-gray-400 dark:text-gray-500">
                        {device.device_os} {device.device_os_version}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 dark:text-white">
                        {device.ou_name || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {device.client_type}
                      </div>
                      {device.client_version && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          v{device.client_version}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(
                          device.status
                        )}`}
                      >
                        {getStatusText(device.status)}
                      </span>
                      {!device.is_active && (
                        <span className="ml-2 px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatLastSeen(device.last_seen, device.minutes_since_last_seen)}
                    </td>
                    {canManageDevices && (
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {device.is_active ? (
                          <button
                            onClick={() => handleDeactivate(device.id)}
                            className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          >
                            Deactivate
                          </button>
                        ) : (
                          <button
                            onClick={() => handleReactivate(device.id)}
                            className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                          >
                            Reactivate
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-gray-50 dark:bg-gray-900 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              Page {page} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
                className="px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-300 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Devices;
