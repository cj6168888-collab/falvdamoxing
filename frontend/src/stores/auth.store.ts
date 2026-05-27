import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { TOKEN_STORAGE_KEY } from '@/lib/api-config';
import { authApi } from '@/api/auth.api';
import type { AuthUser, Tenant, TenantType } from '@/types/auth';

interface AuthStore {
  user: AuthUser | null;
  tenant: Tenant | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  register: (data: {
    username?: string;
    email?: string;
    phone?: string;
    sms_code?: string;
    password: string;
    full_name?: string;
    tenant_name?: string;
    tenant_type: TenantType;
  }) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<boolean>;
  initialize: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
  setTenant: (tenant: Tenant | null) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      tenant: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login(username, password);
          const { user, tenant, tokens } = response;

          localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);

          set({
            user,
            tenant,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true });
        try {
          const request = { ...data, role: 'assistant' as const };
          const response =
            request.phone && request.sms_code
              ? await authApi.registerWithPhone({
                  phone: request.phone,
                  sms_code: request.sms_code,
                  password: request.password,
                  username: request.username,
                  email: request.email,
                  full_name: request.full_name,
                  tenant_name: request.tenant_name,
                  tenant_type: request.tenant_type,
                  role: request.role,
                })
              : await authApi.register(request);
          const { user, tenant, tokens } = response;

          localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);

          set({
            user,
            tenant,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        authApi.logout().catch(() => {});
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        set({
          user: null,
          tenant: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      refreshTokens: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;

        try {
          const tokens = await authApi.refresh(refreshToken);

          localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);

          set({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
          });
          return true;
        } catch {
          get().clearAuth();
          return false;
        }
      },

      initialize: async () => {
        const { accessToken, refreshTokens, user } = get();
        if (!accessToken) {
          set({ isAuthenticated: false, isInitialized: true });
          return;
        }

        if (user) {
          set({ isAuthenticated: true, isInitialized: true });
          return;
        }

        try {
          const freshUser = await authApi.getMe();
          set({ user: freshUser, isAuthenticated: true, isInitialized: true });
        } catch {
          const refreshed = await refreshTokens();
          if (refreshed) {
            try {
              const refreshedUser = await authApi.getMe();
              set({ user: refreshedUser, isAuthenticated: true, isInitialized: true });
            } catch {
              get().clearAuth();
              set({ isInitialized: true });
            }
          } else {
            get().clearAuth();
            set({ isInitialized: true });
          }
        }
      },

      setUser: (user) => set({ user }),
      setTenant: (tenant) => set({ tenant }),
      clearAuth: () => {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        set({
          user: null,
          tenant: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        tenant: state.tenant,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Expose auth state for use by api/client.ts token refresh logic
if (typeof window !== 'undefined') {
  (window as unknown as { __authStore?: { state: Omit<AuthStore, 'login' | 'register' | 'logout' | 'refreshTokens' | 'initialize' | 'setUser' | 'setTenant' | 'clearAuth'> } }).__authStore = {
    get state() {
      return useAuthStore.getState();
    },
  };
}
