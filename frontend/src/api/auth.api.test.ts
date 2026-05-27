import { axiosInstance } from './client';
import { authApi } from './auth.api';
import type { RegisterRequest } from '@/types/auth';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => {
  const mockAxios = {
    get: vi.fn(),
    post: vi.fn(),
  };

  return {
    axiosInstance: mockAxios,
    default: mockAxios,
  };
});

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('auth api', () => {
  it('logs in and normalizes token type', async () => {
    const user = { id: 'user-1', username: 'alice' };
    const tenant = { id: 'tenant-1', name: 'Tenant' };
    mockPost.mockResolvedValueOnce({
      data: {
        success: true,
        user,
        tenant,
        tokens: {
          access_token: 'access',
          refresh_token: 'refresh',
        },
      },
    });

    await expect(authApi.login('alice', 'secret')).resolves.toEqual({
      success: true,
      user,
      tenant,
      tokens: {
        access_token: 'access',
        refresh_token: 'refresh',
        token_type: 'Bearer',
      },
    });
    expect(mockPost).toHaveBeenCalledWith('/api/auth/login', { username: 'alice', password: 'secret' });
  });

  it('registers, refreshes, loads current user, and logs out', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { success: true, user: { id: 'user-1' } } })
      .mockResolvedValueOnce({ data: { success: true, tokens: { access_token: 'next' } } })
      .mockResolvedValueOnce({ data: undefined });
    mockGet.mockResolvedValueOnce({ data: { user: { id: 'user-1' } } });

    const registerRequest: RegisterRequest = {
      username: 'alice',
      email: 'alice@example.com',
      password: 'secret',
      tenant_type: 'law_firm',
    };

    await expect(authApi.register(registerRequest)).resolves.toEqual({
      success: true,
      user: { id: 'user-1' },
    });
    await expect(authApi.refresh('refresh')).resolves.toEqual({ access_token: 'next' });
    await expect(authApi.getMe()).resolves.toEqual({ id: 'user-1' });
    await expect(authApi.logout()).resolves.toBeUndefined();

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/auth/register', registerRequest);
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/auth/refresh', { refresh_token: 'refresh' });
    expect(mockGet).toHaveBeenCalledWith('/api/auth/me');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/auth/logout');
  });

  it('sends sms code, registers with phone, and confirms password reset', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { success: true, message: 'ok', expires_in: 300, debug_code: '123456' } })
      .mockResolvedValueOnce({ data: { success: true, user: { id: 'user-2' } } })
      .mockResolvedValueOnce({ data: { success: true, message: 'reset' } });

    await expect(authApi.sendSmsCode('13800138000', 'register')).resolves.toEqual({
      success: true,
      message: 'ok',
      expires_in: 300,
      debug_code: '123456',
    });
    await expect(
      authApi.registerWithPhone({
        phone: '13800138000',
        sms_code: '123456',
        password: 'secret',
        tenant_type: 'law_firm',
      })
    ).resolves.toEqual({ success: true, user: { id: 'user-2' } });
    await expect(
      authApi.resetPassword({
        phone: '13800138000',
        sms_code: '123456',
        new_password: 'new-secret',
      })
    ).resolves.toBeUndefined();

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/auth/sms/send', {
      phone: '13800138000',
      purpose: 'register',
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/auth/register/phone', {
      phone: '13800138000',
      sms_code: '123456',
      password: 'secret',
      tenant_type: 'law_firm',
    });
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/auth/password-reset/confirm', {
      phone: '13800138000',
      sms_code: '123456',
      new_password: 'new-secret',
    });
  });
});
