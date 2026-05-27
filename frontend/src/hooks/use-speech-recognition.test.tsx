import { renderHook, act } from '@testing-library/react';
import { useSpeechRecognition } from './use-speech-recognition';

interface MockSpeechRecognitionResultEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface MockSpeechRecognitionErrorEvent {
  error: string;
}

function createMockRecognition() {
  return {
    continuous: false,
    interimResults: false,
    lang: '',
    start: vi.fn(),
    stop: vi.fn(),
    onresult: null as ((event: MockSpeechRecognitionResultEvent) => void) | null,
    onerror: null as ((event: MockSpeechRecognitionErrorEvent) => void) | null,
    onend: null as (() => void) | null,
  };
}

describe('useSpeechRecognition', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    delete (window as unknown as Record<string, unknown>).SpeechRecognition;
    delete (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
  });

  it('start begins recognition', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    expect(mockRecognition.start).toHaveBeenCalledTimes(1);
    expect(result.current.isListening).toBe(true);
  });

  it('stop ends recognition', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    expect(result.current.isListening).toBe(true);

    act(() => {
      result.current.stop();
    });

    expect(result.current.isListening).toBe(false);
  });

  it('transcript updates on result', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    act(() => {
      mockRecognition.onresult?.({
        resultIndex: 0,
        results: [{ 0: { transcript: 'Hello world' }, isFinal: true, length: 1 }] as unknown as SpeechRecognitionResultList,
      });
    });

    expect(result.current.transcript).toBe('Hello world');
  });

  it('error handling works correctly', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    act(() => {
      mockRecognition.onerror?.({ error: 'not-allowed' });
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.isListening).toBe(false);
  });

  it('shows error when browser does not support speech recognition', () => {
    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe('Speech recognition not supported');
  });

  it('calls onResult callback with final transcript', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const onResult = vi.fn();
    const { result } = renderHook(() => useSpeechRecognition({ onResult }));

    act(() => {
      result.current.start();
    });

    act(() => {
      mockRecognition.onresult?.({
        resultIndex: 0,
        results: [{ 0: { transcript: 'Final text' }, isFinal: true, length: 1 }] as unknown as SpeechRecognitionResultList,
      });
    });

    expect(onResult).toHaveBeenCalledWith('Final text');
  });

  it('handles interim results', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition());

    act(() => {
      result.current.start();
    });

    act(() => {
      mockRecognition.onresult?.({
        resultIndex: 0,
        results: [{ 0: { transcript: 'Partial' }, isFinal: false, length: 1 }] as unknown as SpeechRecognitionResultList,
      });
    });

    expect(result.current.transcript).toBe('Partial');
  });

  it('sets recognition options correctly', () => {
    const mockRecognition = createMockRecognition();
    function MockSpeechRecognition() {
      return mockRecognition;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;

    const { result } = renderHook(() => useSpeechRecognition({
      continuous: false,
      interimResults: false,
      lang: 'en-US',
    }));

    act(() => {
      result.current.start();
    });

    expect(mockRecognition.continuous).toBe(false);
    expect(mockRecognition.interimResults).toBe(false);
    expect(mockRecognition.lang).toBe('en-US');
  });
});
