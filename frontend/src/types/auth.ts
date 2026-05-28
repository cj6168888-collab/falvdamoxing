// Auth related types

export type UserRole = 'admin' | 'lawyer' | 'assistant' | 'client' | 'viewer';

export type TenantType = 'law_firm' | 'enterprise';

export type SubscriptionPlan = 'free' | 'trial' | 'pro' | 'enterprise' | 'custom';

export type SubscriptionStatus = 'active' | 'past_due' | 'cancelled' | 'suspended';

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  phone: string | null;
  full_name: string | null;
  role: UserRole;
  tenant_id: string;
  is_active: boolean;
  is_email_verified: boolean;
  is_platform_admin: boolean;
  last_login_at: string | null;
  created_at: string | null;
}

export interface Tenant {
  id: string;
  name: string;
  tenant_type: TenantType;
  slug: string;
  logo_url: string | null;
  plan: SubscriptionPlan;
  subscription_status: SubscriptionStatus;
  is_active: boolean;
  created_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  success: boolean;
  user: AuthUser;
  tenant: Tenant;
  tokens: TokenResponse;
}

export interface RegisterRequest {
  username?: string;
  email?: string;
  phone?: string;
  sms_code?: string;
  password: string;
  full_name?: string;
  tenant_name?: string;
  tenant_type: TenantType;
  role?: UserRole;
}

export type SMSPurpose = 'register' | 'password_reset';

export interface SMSCodeResponse {
  success: boolean;
  message: string;
  expires_in: number;
  debug_code?: string;
}

export interface PhoneRegisterRequest {
  phone: string;
  sms_code: string;
  password: string;
  username?: string;
  email?: string;
  full_name?: string;
  tenant_name?: string;
  tenant_type: TenantType;
  role?: UserRole;
}

export interface PasswordResetConfirmRequest {
  phone: string;
  sms_code: string;
  new_password: string;
}

export interface RegisterResponse {
  success: boolean;
  user: AuthUser;
  tenant: Tenant;
  tokens: TokenResponse;
  error?: string;
}

export interface RefreshResponse {
  success: boolean;
  tokens: TokenResponse;
}

export interface AuthState {
  user: AuthUser | null;
  tenant: Tenant | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: '管理员',
  lawyer: '律师',
  assistant: '助理',
  client: '客户',
  viewer: '查看者',
};

export const TENANT_TYPE_LABELS: Record<TenantType, string> = {
  law_firm: '律所',
  enterprise: '企业',
};

export const PLAN_LABELS: Record<SubscriptionPlan, string> = {
  free: '免费版',
  trial: '试用版',
  pro: '专业版',
  enterprise: '企业版',
  custom: '定制版',
};
