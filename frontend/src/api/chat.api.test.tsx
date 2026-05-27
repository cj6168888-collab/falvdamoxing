import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import { getQuickActions, sendChatMessage, useChatHistory } from './chat.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
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
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('chat api hooks', () => {
  it('loads chat history by case id', async () => {
    const history = [{ role: 'assistant', content: 'hello' }];
    mockGet.mockResolvedValueOnce({ data: history });

    const { result } = renderHook(() => useChatHistory('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(history));
    expect(mockGet).toHaveBeenCalledWith('/api/v2/assistant/conversation-history/case-1');
  });

  it('does not request chat history without a case id', () => {
    renderHook(() => useChatHistory(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('chat api commands', () => {
  it('sends a chat message with numeric case id', async () => {
    const response = { data: { message: 'AI response' } };
    mockPost.mockResolvedValueOnce(response);

    await expect(sendChatMessage('12', 'What next?')).resolves.toEqual(response);
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v2/assistant/chat',
      { case_id: 12, message: 'What next?' },
      { timeout: 120000 },
    );
  });

  it('loads quick actions', async () => {
    const actions = [{ id: 'analyze', label: 'Analyze' }];
    mockGet.mockResolvedValueOnce({ data: actions });

    await expect(getQuickActions('case-1')).resolves.toEqual(actions);
    expect(mockGet).toHaveBeenCalledWith('/api/v2/assistant/quick-actions/case-1');
  });
});
