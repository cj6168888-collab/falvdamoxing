import { renderHook, act } from '@testing-library/react';
import { useStreaming } from './use-streaming';

describe('useStreaming', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('start initiates streaming and sets isLoading', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Hello ') })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('World') })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const { result } = renderHook(() => useStreaming());

    await act(async () => {
      await result.current.start('https://api.example.com/stream');
    });

    expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/stream', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }));
    expect(result.current.isLoading).toBe(false);
  });

  it('text accumulates correctly from chunks', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Hello ') })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('World') })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const { result } = renderHook(() => useStreaming());

    await act(async () => {
      await result.current.start('https://api.example.com/stream');
    });

    expect(result.current.text).toBe('Hello World');
  });

  it('stop aborts streaming', async () => {
    const originalAbortController = global.AbortController;
    const abortSpy = vi.fn();
    class MockAbortController {
      abort = abortSpy;
      signal = {};
    }
    vi.stubGlobal('AbortController', MockAbortController);

    const mockReader = {
      read: vi.fn().mockImplementation(() => new Promise(() => {})),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const { result } = renderHook(() => useStreaming());

    await act(async () => {
      result.current.start('https://api.example.com/stream');
    });

    expect(result.current.isLoading).toBe(true);

    act(() => {
      result.current.stop();
    });

    expect(abortSpy).toHaveBeenCalled();

    vi.unstubAllGlobals();
    global.AbortController = originalAbortController;
  });

  it('error handling works correctly', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('Network error'));

    const onError = vi.fn();
    const { result } = renderHook(() => useStreaming({ onError }));

    await act(async () => {
      await result.current.start('https://api.example.com/stream');
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe('Network error');
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
  });

  it('isLoading state management is correct', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('chunk') })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const { result } = renderHook(() => useStreaming());

    expect(result.current.isLoading).toBe(false);

    await act(async () => {
      await result.current.start('https://api.example.com/stream');
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('calls onComplete callback when streaming finishes', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Complete text') })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const onComplete = vi.fn();
    const { result } = renderHook(() => useStreaming({ onComplete }));

    await act(async () => {
      await result.current.start('https://api.example.com/stream');
    });

    expect(onComplete).toHaveBeenCalledWith('Complete text');
  });

  it('calls onChunk callback for each chunk', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('chunk1') })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('chunk2') })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const onChunk = vi.fn();
    const { result } = renderHook(() => useStreaming({ onChunk }));

    await act(async () => {
      await result.current.start('https://api.example.com/stream');
    });

    expect(onChunk).toHaveBeenCalledTimes(2);
    expect(onChunk).toHaveBeenNthCalledWith(1, 'chunk1');
    expect(onChunk).toHaveBeenNthCalledWith(2, 'chunk2');
  });

  it('ignores AbortError on stop', async () => {
    let rejectRead: (reason: Error) => void;
    const mockReader = {
      read: vi.fn().mockImplementation(() => new Promise((_resolve, reject) => {
        rejectRead = reject;
      })),
    };

    vi.spyOn(global, 'fetch').mockResolvedValue({
      body: { getReader: () => mockReader },
    } as unknown as Response);

    const { result } = renderHook(() => useStreaming());

    await act(async () => {
      result.current.start('https://api.example.com/stream');
    });

    await act(async () => {
      result.current.stop();
      rejectRead(new DOMException('The operation was aborted.', 'AbortError'));
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.error).toBeNull();
  });
});
