import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth.store';

export function useAuth() {
  const {
    user,
    tenant,
    isAuthenticated,
    isLoading,
    isInitialized,
    login,
    register,
    logout,
    initialize,
    refreshTokens,
  } = useAuthStore();

  return {
    user,
    tenant,
    isAuthenticated,
    isLoading,
    isInitialized,
    login,
    register,
    logout,
    initialize,
    refreshTokens,
  };
}

export function useAuthInit() {
  const { initialize, isInitialized } = useAuthStore();

  useEffect(() => {
    if (!isInitialized) {
      initialize();
    }
  }, [initialize, isInitialized]);
}

export function useRequireAuth(redirectTo = '/login') {
  const navigate = useNavigate();
  const { isAuthenticated, isInitialized } = useAuthStore();

  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, isInitialized, navigate, redirectTo]);

  return { isAuthenticated, isInitialized };
}
