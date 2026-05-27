import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import { useSeniorAnalysis } from './senior-analysis.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn(),
  },
}));

const mockPost = axiosInstance.post as Mock;

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
  mockPost.mockReset();
});

describe('senior analysis api', () => {
  it('starts senior analysis with parsed case id and depth', async () => {
    mockPost.mockResolvedValueOnce({ data: { summary: 'analysis' } });

    const { result } = renderHook(() => useSeniorAnalysis('12', 'deep'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual({ summary: 'analysis' }));
    expect(mockPost).toHaveBeenCalledWith('/api/v2/senior-analysis/analyze', {
      case_id: 12,
      analysis_level: 'deep',
    });
  });

  it('does not start senior analysis without a case id', () => {
    renderHook(() => useSeniorAnalysis(''), { wrapper: createWrapper() });

    expect(mockPost).not.toHaveBeenCalled();
  });
});
