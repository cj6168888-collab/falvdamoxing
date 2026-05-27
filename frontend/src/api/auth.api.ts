import { axiosInstance } from './client';
import type {
  LoginResponse,
  PasswordResetConfirmRequest,
  PhoneRegisterRequest,
  RegisterRequest,
  RegisterResponse,
  AuthUser,
  SMSCodeResponse,
  SMSPurpose,
  Tenant,
  TokenResponse,
} from '@/types/auth';

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await axiosInstance.post<{ success: boolean; user: AuthUser; tenant: Tenant; tokens: TokenResponse }>(
      '/api/auth/login',
      { username, password }
    );
    // Backend returns { success, user, tenant, tokens } - flatten to match LoginResponse
    const data = response.data;
    return {
      success: data.success,
      user: data.user,
      tenant: data.tenant,
      tokens: {
        ...data.tokens,
        token_type: data.tokens.token_type || 'Bearer',
      },
    };
  },

  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const response = await axiosInstance.post<RegisterResponse>('/api/auth/register', data);
    return response.data;
  },

  sendSmsCode: async (phone: string, purpose: SMSPurpose): Promise<SMSCodeResponse> => {
    const response = await axiosInstance.post<SMSCodeResponse>('/api/auth/sms/send', {
      phone,
      purpose,
    });
    return response.data;
  },

  registerWithPhone: async (data: PhoneRegisterRequest): Promise<RegisterResponse> => {
    const response = await axiosInstance.post<RegisterResponse>('/api/auth/register/phone', data);
    return response.data;
  },

  resetPassword: async (data: PasswordResetConfirmRequest): Promise<void> => {
    await axiosInstance.post('/api/auth/password-reset/confirm', data);
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await axiosInstance.post<{ success: boolean; tokens: TokenResponse }>(
      '/api/auth/refresh',
      { refresh_token: refreshToken }
    );
    return response.data.tokens;
  },

  getMe: async (): Promise<AuthUser> => {
    const response = await axiosInstance.get<{ user: AuthUser }>('/api/auth/me');
    return response.data.user;
  },

  logout: async (): Promise<void> => {
    await axiosInstance.post('/api/auth/logout');
  },
};
