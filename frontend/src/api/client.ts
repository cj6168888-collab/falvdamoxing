import axios from 'axios';
import type {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import {
  API_BASE_URL,
  API_RETRY_COUNT,
  API_RETRY_DELAY_MS,
  API_TIMEOUT,
  TOKEN_STORAGE_KEY,
} from '../lib/api-config';

export class ApiError extends Error {
  public status: number;
  public code: string;
  public details: unknown;

  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class NetworkError extends Error {
  constructor(message = '网络连接失败，请检查网络设置') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = '未授权，请重新登录') {
    super(message, 401, 'UNAUTHORIZED');
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends ApiError {
  constructor(message = '无权限执行此操作') {
    super(message, 403, 'FORBIDDEN');
    this.name = 'ForbiddenError';
  }
}

export class ServerError extends ApiError {
  constructor(message: string, status: number, details?: unknown) {
    super(message, status, 'SERVER_ERROR', details);
    this.name = 'ServerError';
  }
}

function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function isRetryable(status: number): boolean {
  return status >= 500 || status === 429 || status === 0;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retryCount?: number;
}

async function retryRequest<T>(
  config: RetryableConfig,
  retries: number,
  attempt: number,
): Promise<AxiosResponse<T>> {
  if (attempt >= retries) {
    throw new ServerError('请求失败，已达到最大重试次数', 500);
  }

  const delay = API_RETRY_DELAY_MS * 2 ** attempt;
  await sleep(delay);

  try {
    return await axiosInstance.request<T>({ ...config });
  } catch (error) {
    const axiosError = error as AxiosError;
    const status = axiosError.response?.status ?? 0;

    if (!isRetryable(status)) {
      throw error;
    }

    return retryRequest<T>(config, retries, attempt + 1);
  }
}

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}

function clearAuthAndRedirect() {
  isRefreshing = false;
  refreshSubscribers = [];
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // localStorage may be unavailable in restricted browser contexts.
  }

  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
}

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (!navigator.onLine) {
      throw new NetworkError();
    }

    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: unknown) => Promise.reject(error),
);

axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: unknown) => {
    const axiosError = error as AxiosError<{ detail?: string; message?: string; code?: string }>;
    const originalConfig = axiosError.config as RetryableConfig | undefined;

    if (!originalConfig) {
      return Promise.reject(new ApiError('请求配置丢失', 0, 'CONFIG_ERROR'));
    }

    const status = axiosError.response?.status ?? 0;
    const responseData = axiosError.response?.data;
    const message = responseData?.detail || responseData?.message || '请求失败';
    const code = responseData?.code || 'UNKNOWN';

    if (!navigator.onLine) {
      return Promise.reject(new NetworkError());
    }

    if (isRetryable(status) && originalConfig._retryCount === undefined) {
      originalConfig._retryCount = 0;
    }

    const retryCount = originalConfig._retryCount ?? 0;

    if (isRetryable(status) && retryCount < API_RETRY_COUNT) {
      originalConfig._retryCount = retryCount + 1;
      return retryRequest(originalConfig, API_RETRY_COUNT, retryCount);
    }

    if (status === 401) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken: string) => {
            originalConfig.headers.Authorization = `Bearer ${newToken}`;
            resolve(axiosInstance(originalConfig).then((response) => response).catch(reject));
          });
        });
      }

      const authStoreState = (window as unknown as {
        __authStore?: { state: { refreshToken?: string } };
      }).__authStore;
      const refreshToken = authStoreState?.state?.refreshToken;

      if (refreshToken) {
        isRefreshing = true;

        try {
          const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (response.ok) {
            const data = await response.json();
            const newAccessToken = data.tokens?.access_token || data.access_token;
            if (newAccessToken) {
              localStorage.setItem(TOKEN_STORAGE_KEY, newAccessToken);
              onTokenRefreshed(newAccessToken);
              isRefreshing = false;

              originalConfig.headers.Authorization = `Bearer ${newAccessToken}`;
              return axiosInstance(originalConfig);
            }
          }

          clearAuthAndRedirect();
          return Promise.reject(new UnauthorizedError());
        } catch {
          clearAuthAndRedirect();
          return Promise.reject(new UnauthorizedError());
        }
      }

      clearAuthAndRedirect();
      return Promise.reject(new UnauthorizedError());
    }

    if (status === 403) {
      return Promise.reject(new ForbiddenError(message));
    }

    if (status >= 500) {
      console.error('[API] Server error:', status, responseData);
      return Promise.reject(new ServerError(message, status, responseData));
    }

    console.error('[API] Other error:', status, responseData);
    return Promise.reject(new ApiError(message, status, code, responseData));
  },
);

export { axiosInstance };
export default axiosInstance;
