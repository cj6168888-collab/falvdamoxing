import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useCaseProfile } from './use-profile';
import { useProfileStore } from '@/stores/profile.store';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useCaseProfile', () => {
  beforeEach(() => {
    useProfileStore.setState({ profiles: {}, setProfile: vi.fn(), getProfile: vi.fn() });
  });

  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useCaseProfile('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('profile');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('isError');
  });
});
