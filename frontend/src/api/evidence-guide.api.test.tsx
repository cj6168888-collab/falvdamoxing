import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import { answerGuideQuestion, useEvidenceGuide } from './evidence-guide.api';
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

describe('evidence guide api', () => {
  it('loads evidence guide diagnosis', async () => {
    mockPost.mockResolvedValueOnce({ data: { questions: [] } });

    const { result } = renderHook(() => useEvidenceGuide('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual({ questions: [] }));
    expect(mockPost).toHaveBeenCalledWith('/api/v2/evidence-guide/diagnose', {
      case_id: 12,
      force_refresh: true,
    });
  });

  it('does not request evidence guide without a case id', () => {
    renderHook(() => useEvidenceGuide(''), { wrapper: createWrapper() });

    expect(mockPost).not.toHaveBeenCalled();
  });

  it('submits guide question answers', async () => {
    mockPost.mockResolvedValueOnce({ data: { next: 2 } });

    await expect(answerGuideQuestion('12', 'q-1', 'answer')).resolves.toEqual({ next: 2 });
    expect(mockPost).toHaveBeenCalledWith('/api/v2/evidence-guide/question/answer', {
      case_id: 12,
      question_id: 'q-1',
      answer: 'answer',
    });
  });
});
