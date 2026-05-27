import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useFinance } from './use-finance';
import axiosInstance from '@/api/client';

vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
    get: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useFinance', () => {
  it('fetches finance data for case', async () => {
    vi.mocked(axiosInstance.get).mockResolvedValueOnce({ data: { balance: 10000 } });
    const { result } = renderHook(() => useFinance('case-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });
  });

  it('does not fetch when caseId is empty', async () => {
    const { result } = renderHook(() => useFinance(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toBeUndefined();
  });

  it('returns finance object', async () => {
    vi.mocked(axiosInstance.get).mockResolvedValueOnce({ data: { balance: 0 } });
    const { result } = renderHook(() => useFinance('case-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });
  });

  it('handles fetch error', async () => {
    vi.mocked(axiosInstance.get).mockRejectedValueOnce(new Error('Not found'));
    const { result } = renderHook(() => useFinance('invalid-case'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
