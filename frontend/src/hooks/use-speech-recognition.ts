import { useState, useCallback } from 'react';

interface UseSpeechRecognitionOptions {
  onResult?: (text: string) => void;
  onError?: (error: Error) => void;
  continuous?: boolean;
  interimResults?: boolean;
  lang?: string;
}

interface SpeechRecognitionResultEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorPayload {
  error: string;
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorPayload) => void) | null;
  onend: (() => void) | null;
  start: () => void;
}

interface SpeechRecognitionWindow {
  SpeechRecognition?: { new (): SpeechRecognitionInstance };
  webkitSpeechRecognition?: { new (): SpeechRecognitionInstance };
}

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<Error | null>(null);

  const start = useCallback(() => {
    const SpeechRecognition = (window as unknown as SpeechRecognitionWindow).SpeechRecognition ||
      (window as unknown as SpeechRecognitionWindow).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      const err = new Error('Speech recognition not supported');
      setError(err);
      options.onError?.(err);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = options.continuous ?? true;
    recognition.interimResults = options.interimResults ?? true;
    recognition.lang = options.lang ?? 'zh-CN';

    recognition.onresult = (event: SpeechRecognitionResultEvent) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += t;
        } else {
          interimTranscript += t;
        }
      }

      setTranscript(finalTranscript || interimTranscript);
      if (finalTranscript) {
        options.onResult?.(finalTranscript);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorPayload) => {
      const err = new Error(event.error);
      setError(err);
      options.onError?.(err);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
    setIsListening(true);
  }, [options]);

  const stop = useCallback(() => {
    setIsListening(false);
  }, []);

  return { isListening, transcript, error, start, stop };
}
