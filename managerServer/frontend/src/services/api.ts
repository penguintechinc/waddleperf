import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  User,
  OrganizationUnit,
  CreateUserRequest,
  UpdateUserRequest,
  ChangePasswordRequest,
  CreateOrganizationRequest,
  MfaSetupResponse,
  TestResult,
  ApiError
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(
      (config) => {
        const accessToken = localStorage.getItem('access_token');
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                refresh_token: refreshToken
              });
              const newAccessToken = response.data.access_token;
              localStorage.setItem('access_token', newAccessToken);

              if (error.config) {
                error.config.headers.Authorization = `Bearer ${newAccessToken}`;
                return this.client(error.config);
              }
            } catch (refreshError) {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('user');
              if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
              }
            }
          } else {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            if (!window.location.pathname.includes('/login')) {
              window.location.href = '/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/v1/auth/login', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/api/v1/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  async setupMfa(): Promise<MfaSetupResponse> {
    const response = await this.client.post<MfaSetupResponse>('/api/v1/auth/mfa/setup');
    return response.data;
  }

  async verifyMfa(code: string): Promise<{ message: string }> {
    const response = await this.client.post('/api/v1/auth/mfa/verify', { mfa_token: code });
    return response.data;
  }

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/api/v1/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/api/v1/auth/reset-password', { token, new_password: newPassword });
    return response.data;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/api/v1/auth/change-password', { current_password: currentPassword, new_password: newPassword });
    return response.data;
  }

  async listUsers(page = 1, perPage = 50): Promise<{ users: User[]; total: number; page: number; per_page: number }> {
    const response = await this.client.get('/api/v1/users', {
      params: { page, per_page: perPage }
    });
    return response.data;
  }

  async getUser(userId: number): Promise<User> {
    const response = await this.client.get<User>(`/api/v1/users/${userId}`);
    return response.data;
  }

  async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await this.client.post<User>('/api/v1/users', userData);
    return response.data;
  }

  async updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
    const response = await this.client.put<User>(`/api/v1/users/${userId}`, userData);
    return response.data;
  }

  async changeUserPassword(userId: number, data: ChangePasswordRequest): Promise<{ message: string }> {
    const response = await this.client.put(`/api/v1/users/${userId}/password`, data);
    return response.data;
  }

  async deleteUser(userId: number): Promise<{ message: string }> {
    const response = await this.client.delete(`/api/v1/users/${userId}`);
    return response.data;
  }

  async listOrganizations(): Promise<{ organizations: OrganizationUnit[] }> {
    const response = await this.client.get('/api/v1/orgs');
    return response.data;
  }

  async getOrganization(orgId: number): Promise<OrganizationUnit> {
    const response = await this.client.get<OrganizationUnit>(`/api/v1/orgs/${orgId}`);
    return response.data;
  }

  async createOrganization(orgData: CreateOrganizationRequest): Promise<OrganizationUnit> {
    const response = await this.client.post<OrganizationUnit>('/api/v1/orgs', orgData);
    return response.data;
  }

  async getRecentTests(limit = 100): Promise<{ results: TestResult[] }> {
    const response = await this.client.get('/api/v1/stats/recent', {
      params: { limit }
    });
    return response.data;
  }

  async getDeviceStats(deviceId: string): Promise<{ device: string; statistics: any[] }> {
    const response = await this.client.get('/api/v1/stats/by-device', {
      params: { device_id: deviceId }
    });
    return response.data;
  }

  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const api = new ApiService();
export default api;
