export type UserRole = 'global_admin' | 'global_reporter' | 'ou_admin' | 'ou_reporter' | 'user';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  ou_id: number | null;
  mfa_enabled: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  api_key?: string;
  mfa_secret?: string;
}

export interface OrganizationUnit {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  mfa_code?: string;
}

export interface LoginResponse {
  token: string;
  user: User;
  expires_in: number;
}

export interface MfaSetupResponse {
  secret: string;
  qr_uri: string;
}

export interface TestResult {
  id: number;
  device_serial: string;
  test_type: string;
  result_data: any;
  created_at: string;
  latency?: number;
  bandwidth?: number;
  success?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role?: UserRole;
  ou_id?: number;
}

export interface UpdateUserRequest {
  email?: string;
  role?: UserRole;
  ou_id?: number;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  password: string;
}

export interface CreateOrganizationRequest {
  name: string;
  description?: string;
}

export interface ApiError {
  error: string;
  mfa_required?: boolean;
}

export type ThemeMode = 'light' | 'dark' | 'auto';
