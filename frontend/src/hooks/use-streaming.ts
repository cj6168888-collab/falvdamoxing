import { useState, useCallback, useRef } from 'react';

interface UseStreamingOptions {
  onChunk?: (chunk: string) => void;
  onComplete?: (fullText: string) => void;
  onError?: (error: Error) => void;
}

export function useStreaming(options: UseStreamingOptions = {}) {
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback(
    async (url: string, body?: unknown) => {
      setIsLoading(true);
      setError(null);
      setText('');

      const abortController = new AbortController();
      abortRef.current = abortController;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body ? JSON.stringify(body) : undefined,
          signal: abortController.signal,
        });

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let fullText = '';

        while (reader) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          fullText += chunk;
          setText(fullText);
          options.onChunk?.(chunk);
        }

        options.onComplete?.(fullText);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err);
          options.onError?.(err);
        }
      } finally {
        setIsLoading(false);
        abortRef.current = null;
      }
    },
    [options]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { text, isLoading, error, start, stop };
}
