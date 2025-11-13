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
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
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
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }

  async setupMfa(): Promise<MfaSetupResponse> {
    const response = await this.client.post<MfaSetupResponse>('/api/v1/auth/mfa/setup');
    return response.data;
  }

  async verifyMfa(code: string): Promise<{ message: string }> {
    const response = await this.client.post('/api/v1/auth/mfa/verify', { code });
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

  async changePassword(userId: number, data: ChangePasswordRequest): Promise<{ message: string }> {
    const response = await this.client.put(`/api/v1/users/${userId}/password`, data);
    return response.data;
  }

  async deleteUser(userId: number): Promise<{ message: string }> {
    const response = await this.client.delete(`/api/v1/users/${userId}`);
    return response.data;
  }

  async listOrganizations(): Promise<{ organizations: OrganizationUnit[] }> {
    const response = await this.client.get('/api/v1/organizations');
    return response.data;
  }

  async getOrganization(orgId: number): Promise<OrganizationUnit> {
    const response = await this.client.get<OrganizationUnit>(`/api/v1/organizations/${orgId}`);
    return response.data;
  }

  async createOrganization(orgData: CreateOrganizationRequest): Promise<OrganizationUnit> {
    const response = await this.client.post<OrganizationUnit>('/api/v1/organizations', orgData);
    return response.data;
  }

  async getRecentTests(limit = 100): Promise<{ results: TestResult[] }> {
    const response = await this.client.get('/api/v1/statistics/recent', {
      params: { limit }
    });
    return response.data;
  }

  async getDeviceStats(deviceSerial: string): Promise<{ device: string; statistics: any[] }> {
    const response = await this.client.get(`/api/v1/statistics/device/${deviceSerial}`);
    return response.data;
  }

  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const api = new ApiService();
export default api;
