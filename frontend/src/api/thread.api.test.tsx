import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  createCounterClaim,
  createThread,
  updateCounterClaim,
  updateThread,
  useCounterClaims,
  useThreads,
} from './thread.api';
import type { ReactNode } from 'react';
import type { CaseThread, CounterClaim } from '@/types/thread.types';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;
const mockPut = axiosInstance.put as Mock;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
});

describe('thread api', () => {
  it('loads threads and counter claims', async () => {
    mockGet.mockImplementation((url: string) => Promise.resolve({
      data: url.includes('counter-claims') ? [{ id: 'claim-1' }] : [{ id: 'thread-1' }],
    }));

    const threadsHook = renderHook(() => useThreads('case-1'), { wrapper: createWrapper() });
    const claimsHook = renderHook(() => useCounterClaims('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(threadsHook.result.current.data).toEqual([{ id: 'thread-1' }]));
    await waitFor(() => expect(claimsHook.result.current.data).toEqual([{ id: 'claim-1' }]));

    expect(mockGet).toHaveBeenCalledWith('/api/cases/case-1/threads');
    expect(mockGet).toHaveBeenCalledWith('/api/cases/case-1/counter-claims');
  });

  it('does not request resources without a case id', () => {
    renderHook(() => useThreads(''), { wrapper: createWrapper() });
    renderHook(() => useCounterClaims(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('creates and updates threads and counter claims', async () => {
    mockPost.mockResolvedValue({ data: { id: 'created' } });
    mockPut.mockResolvedValue({ data: { id: 'updated' } });

    const newThread: Partial<CaseThread> = { title: 'thread' };
    const threadUpdate: Partial<CaseThread> = { title: 'updated' };
    const newClaim: Partial<CounterClaim> = { title: 'claim' };
    const claimUpdate: Partial<CounterClaim> = { title: 'claim updated' };

    await expect(createThread('case-1', newThread)).resolves.toEqual({ id: 'created' });
    await expect(updateThread('case-1', 'thread-1', threadUpdate)).resolves.toEqual({ id: 'updated' });
    await expect(createCounterClaim('case-1', newClaim)).resolves.toEqual({ id: 'created' });
    await expect(updateCounterClaim('case-1', 'claim-1', claimUpdate)).resolves.toEqual({ id: 'updated' });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/cases/case-1/threads', newThread);
    expect(mockPut).toHaveBeenNthCalledWith(1, '/api/cases/case-1/threads/thread-1', threadUpdate);
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/cases/case-1/counter-claims', newClaim);
    expect(mockPut).toHaveBeenNthCalledWith(2, '/api/cases/case-1/counter-claims/claim-1', claimUpdate);
  });
});
