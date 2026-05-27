import { useState, useCallback, useRef, useEffect } from 'react';

export type TTSStatus = 'idle' | 'speaking' | 'paused' | 'loading';

export interface UseTextToSpeechOptions {
  /** 语速，0.1 - 10，默认 1 */
  rate?: number;
  /** 音调，0.1 - 2，默认 1 */
  pitch?: number;
  /** 音量，0 - 1，默认 1 */
  volume?: number;
  /** 语言，默认 zh-CN */
  lang?: string;
  /** 语音合成开始回调 */
  onStart?: () => void;
  /** 语音合成结束回调 */
  onEnd?: () => void;
  /** 语音合成错误回调 */
  onError?: (error: Error) => void;
  /** 语音合成暂停回调 */
  onPause?: () => void;
  /** 语音合成恢复回调 */
  onResume?: () => void;
}

export interface UseTextToSpeechReturn {
  /** 当前状态 */
  status: TTSStatus;
  /** 正在播放的文本 */
  currentText: string;
  /** 当前进度（0-1） */
  progress: number;
  /** 错误信息 */
  error: Error | null;
  /** 播放文本 */
  speak: (text: string) => void;
  /** 暂停播放 */
  pause: () => void;
  /** 恢复播放 */
  resume: () => void;
  /** 停止播放 */
  stop: () => void;
  /** 切换播放/暂停状态 */
  toggle: (text: string) => void;
  /** 获取可用语音列表 */
  getVoices: () => SpeechSynthesisVoice[];
  /** 是否支持语音合成 */
  isSupported: boolean;
}

export function useTextToSpeech(options: UseTextToSpeechOptions = {}): UseTextToSpeechReturn {
  const {
    rate = 1,
    pitch = 1,
    volume = 1,
    lang = 'zh-CN',
    onStart,
    onEnd,
    onError,
    onPause,
    onResume,
  } = options;

  const [status, setStatus] = useState<TTSStatus>('idle');
  const [currentText, setCurrentText] = useState('');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<Error | null>(null);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const startTimeRef = useRef<number>(0);
  const estimatedDurationRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);

  // 检查浏览器支持
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  // 清理函数
  const cleanup = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setProgress(0);
  }, []);

  // 更新进度
  const updateProgress = useCallback(() => {
    if (status !== 'speaking' || !startTimeRef.current) {
      return;
    }

    const elapsed = Date.now() - startTimeRef.current;
    const newProgress = Math.min(elapsed / estimatedDurationRef.current, 1);
    setProgress(newProgress);

    if (newProgress < 1) {
      animationFrameRef.current = requestAnimationFrame(updateProgress);
    }
  }, [status]);

  // 停止播放
  const stop = useCallback(() => {
    cleanup();
    setStatus('idle');
    setCurrentText('');
    setError(null);
  }, [cleanup]);

  // 播放文本
  const speak = useCallback(
    (text: string) => {
      if (!isSupported) {
        const err = new Error('当前浏览器不支持语音合成');
        setError(err);
        onError?.(err);
        return;
      }

      // 停止之前的播放
      cleanup();

      setCurrentText(text);
      setStatus('loading');
      setError(null);

      const utterance = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utterance;

      // 设置语音参数
      utterance.rate = rate;
      utterance.pitch = pitch;
      utterance.volume = volume;
      utterance.lang = lang;

      // 估算播放时长（基于文本长度和语速）
      const wordsPerMinute = 150 * rate; // 基础语速
      const wordCount = text.replace(/\s+/g, '').length;
      estimatedDurationRef.current = (wordCount / wordsPerMinute) * 60 * 1000;
      startTimeRef.current = Date.now();

      // 获取语音
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) => v.lang.includes('zh') || v.lang.includes('CN')
      );
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      // 事件处理
      utterance.onstart = () => {
        setStatus('speaking');
        onStart?.();
        animationFrameRef.current = requestAnimationFrame(updateProgress);
      };

      utterance.onend = () => {
        setStatus('idle');
        setProgress(1);
        setCurrentText('');
        cleanup();
        onEnd?.();
      };

      utterance.onerror = (event) => {
        const err = new Error(event.error || '语音合成失败');
        setError(err);
        setStatus('idle');
        cleanup();
        onError?.(err);
      };

      utterance.onpause = () => {
        setStatus('paused');
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        onPause?.();
      };

      utterance.onresume = () => {
        setStatus('speaking');
        // 重新计算开始时间以保持进度
        const elapsed = Date.now() - startTimeRef.current;
        startTimeRef.current = Date.now() - elapsed;
        animationFrameRef.current = requestAnimationFrame(updateProgress);
        onResume?.();
      };

      // 开始播放
      window.speechSynthesis.speak(utterance);
    },
    [isSupported, rate, pitch, volume, lang, cleanup, onStart, onEnd, onError, onPause, onResume, updateProgress]
  );

  // 暂停播放
  const pause = useCallback(() => {
    if (window.speechSynthesis && status === 'speaking') {
      window.speechSynthesis.pause();
    }
  }, [status]);

  // 恢复播放
  const resume = useCallback(() => {
    if (window.speechSynthesis && status === 'paused') {
      window.speechSynthesis.resume();
    }
  }, [status]);

  // 切换播放/暂停
  const toggle = useCallback(
    (text: string) => {
      if (status === 'idle') {
        speak(text);
      } else if (status === 'speaking') {
        pause();
      } else if (status === 'paused') {
        resume();
      }
    },
    [status, speak, pause, resume]
  );

  // 获取可用语音列表
  const getVoices = useCallback(() => {
    if (!isSupported) return [];
    return window.speechSynthesis.getVoices();
  }, [isSupported]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    status,
    currentText,
    progress,
    error,
    speak,
    pause,
    resume,
    stop,
    toggle,
    getVoices,
    isSupported,
  };
}
