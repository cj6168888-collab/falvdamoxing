import { renderHook, act } from '@testing-library/react';
import { useChatStore } from './chat.store';
import type { ChatMessage } from '@/types/chat.types';

vi.mock('zustand/middleware', async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    persist: (creator: unknown) => creator,
  };
});

const mockMessage: ChatMessage = {
  id: 'msg-1',
  role: 'user',
  content: 'Hello',
  timestamp: '2024-01-01T00:00:00Z',
};

describe('useChatStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.setState({ conversations: {} });
  });

  it('initializes with empty conversations', () => {
    const { result } = renderHook(() => useChatStore());
    expect(result.current.conversations).toEqual({});
  });

  it('adds a message to a conversation', () => {
    const { result } = renderHook(() => useChatStore());
    act(() => {
      result.current.addMessage('case-1', mockMessage);
    });
    expect(result.current.conversations['case-1']).toHaveLength(1);
    expect(result.current.conversations['case-1'][0]).toEqual(mockMessage);
  });

  it('appends messages to existing conversation', () => {
    const { result } = renderHook(() => useChatStore());
    const msg2: ChatMessage = { id: 'msg-2', role: 'assistant', content: 'Hi', timestamp: '2024-01-01T00:00:00Z' };
    act(() => {
      result.current.addMessage('case-1', mockMessage);
    });
    act(() => {
      result.current.addMessage('case-1', msg2);
    });
    expect(result.current.conversations['case-1']).toHaveLength(2);
  });

  it('keeps conversations separate by caseId', () => {
    const { result } = renderHook(() => useChatStore());
    const msg2: ChatMessage = { id: 'msg-2', role: 'assistant', content: 'Hi', timestamp: '2024-01-01T00:00:00Z' };
    act(() => {
      result.current.addMessage('case-1', mockMessage);
    });
    act(() => {
      result.current.addMessage('case-2', msg2);
    });
    expect(result.current.conversations['case-1']).toHaveLength(1);
    expect(result.current.conversations['case-2']).toHaveLength(1);
  });

  it('clears a conversation', () => {
    const { result } = renderHook(() => useChatStore());
    act(() => {
      result.current.addMessage('case-1', mockMessage);
    });
    expect(result.current.conversations['case-1']).toHaveLength(1);
    act(() => {
      result.current.clearConversation('case-1');
    });
    expect(result.current.conversations['case-1']).toEqual([]);
  });
});
