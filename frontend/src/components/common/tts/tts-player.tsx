import { useEffect, useState } from 'react';
import { useTextToSpeech } from '@/hooks/use-text-to-speech';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Label } from '@/components/ui/label';
import {
  Play,
  Pause,
  Square,
  Volume2,
  VolumeX,
  Settings,
  Loader2,
} from 'lucide-react';

interface TTSPlayerProps {
  /** 要朗读的文本 */
  text: string;
  /** 是否自动播放 */
  autoPlay?: boolean;
  /** 是否显示设置按钮 */
  showSettings?: boolean;
  /** 播放器大小 */
  size?: 'sm' | 'md' | 'lg';
  /** 类名 */
  className?: string;
}

export function TTSPlayer({
  text,
  autoPlay = false,
  showSettings = true,
  size = 'md',
  className = '',
}: TTSPlayerProps) {
  const [rate, setRate] = useState([1]);
  const [volume, setVolume] = useState([1]);
  const [muted, setMuted] = useState(false);

  const {
    status,
    progress,
    error,
    speak,
    stop,
    toggle,
    isSupported,
  } = useTextToSpeech({
    rate: rate[0],
    volume: muted ? 0 : volume[0],
    lang: 'zh-CN',
    onEnd: () => {},
    onError: (err) => console.error('TTS Error:', err),
  });

  const handlePlay = () => {
    toggle(text);
  };

  useEffect(() => {
    if (autoPlay && status === 'idle' && text.trim()) {
      speak(text);
    }
  }, [autoPlay, speak, status, text]);

  const handleStop = () => {
    stop();
  };

  const isPlaying = status === 'speaking';
  const isPaused = status === 'paused';
  const isLoading = status === 'loading';

  const sizeClasses = {
    sm: 'h-8 text-xs',
    md: 'h-10 text-sm',
    lg: 'h-12 text-base',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  if (!isSupported) {
    return (
      <Badge variant="outline" className={`${sizeClasses[size]} ${className}`}>
        浏览器不支持语音合成
      </Badge>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* 主播放按钮 */}
      <Button
        variant={isPlaying ? 'default' : 'outline'}
        size="icon"
        className={sizeClasses[size]}
        onClick={handlePlay}
        disabled={isLoading}
        title={isPlaying ? '暂停' : '播放'}
      >
        {isLoading ? (
          <Loader2 className={`${iconSizes[size]} animate-spin`} />
        ) : isPlaying ? (
          <Pause className={iconSizes[size]} />
        ) : (
          <Play className={iconSizes[size]} />
        )}
      </Button>

      {/* 停止按钮 */}
      {(isPlaying || isPaused) && (
        <Button
          variant="outline"
          size="icon"
          className={sizeClasses[size]}
          onClick={handleStop}
          title="停止"
        >
          <Square className={iconSizes[size]} />
        </Button>
      )}

      {/* 静音按钮 */}
      {showSettings && (
        <Button
          variant="ghost"
          size="icon"
          className={sizeClasses[size]}
          onClick={() => setMuted(!muted)}
          title={muted ? '取消静音' : '静音'}
        >
          {muted ? (
            <VolumeX className={iconSizes[size]} />
          ) : (
            <Volume2 className={iconSizes[size]} />
          )}
        </Button>
      )}

      {/* 进度条 */}
      {(isPlaying || isPaused) && (
        <div className="flex-1 min-w-[100px]">
          <Progress value={progress * 100} className="h-1" />
        </div>
      )}

      {/* 状态标签 */}
      {status !== 'idle' && (
        <Badge variant="outline" className={`${sizeClasses[size]} capitalize`}>
          {status === 'loading' ? '加载中' : status === 'speaking' ? '朗读中' : '已暂停'}
        </Badge>
      )}

      {/* 设置面板 */}
      {showSettings && (
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="ghost" size="icon" className={sizeClasses[size]}>
              <Settings className={iconSizes[size]} />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-64" align="end">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs">语速</Label>
                  <span className="text-xs text-muted-foreground">{rate[0]}x</span>
                </div>
                <Slider
                  value={rate}
                  onValueChange={setRate}
                  min={0.5}
                  max={2}
                  step={0.1}
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>慢</span>
                  <span>正常</span>
                  <span>快</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs">音量</Label>
                  <span className="text-xs text-muted-foreground">
                    {Math.round(volume[0] * 100)}%
                  </span>
                </div>
                <Slider
                  value={volume}
                  onValueChange={setVolume}
                  min={0}
                  max={1}
                  step={0.1}
                />
              </div>

              {error && (
                <p className="text-xs text-destructive">{error.message}</p>
              )}
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}
