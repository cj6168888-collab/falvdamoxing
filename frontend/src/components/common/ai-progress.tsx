import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Loader2, Sparkles, CheckCircle2, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIProgressProps {
  /** 是否正在执行 AI 任务 */
  isActive: boolean;
  /** 任务标题 */
  title?: string;
  /** 预计耗时（毫秒），用于倒计时 */
  estimatedDuration?: number;
  /** 任务完成后的回调 */
  onComplete?: () => void;
  /** 自定义步骤列表（如果不提供则使用默认步骤） */
  steps?: string[];
  /** 步骤切换间隔（毫秒） */
  stepInterval?: number;
  className?: string;
}

const DEFAULT_STEPS = [
  '正在分析案件信息...',
  '正在检索相关法律依据...',
  '正在提取关键证据...',
  '正在构建逻辑框架...',
  '正在生成内容...',
  '正在进行质量校验...',
  '即将完成...',
];

export function AIProgress({
  isActive,
  title = 'AI 处理中',
  estimatedDuration = 30000,
  onComplete,
  steps = DEFAULT_STEPS,
  stepInterval,
  className,
}: AIProgressProps) {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(estimatedDuration);
  const [startTime, setStartTime] = useState<number | null>(null);

  const autoStepInterval = stepInterval || Math.floor(estimatedDuration / steps.length);

  // Reset when task starts
  useEffect(() => {
    if (isActive) {
      setProgress(0);
      setCurrentStep(0);
      setTimeRemaining(estimatedDuration);
      setStartTime(Date.now());
    }
  }, [isActive, estimatedDuration]);

  // Progress simulation
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        // Non-linear progress: starts fast, slows down, then finishes
        const increment = prev < 30 ? 2 : prev < 70 ? 1 : prev < 90 ? 0.5 : 0.3;
        const next = Math.min(prev + increment, 99);
        return next;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [isActive]);

  // Step rotation
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        const next = Math.min(prev + 1, steps.length - 1);
        return next;
      });
    }, autoStepInterval);

    return () => clearInterval(interval);
  }, [isActive, steps.length, autoStepInterval]);

  // Countdown timer
  useEffect(() => {
    if (!isActive || !startTime) return;

    const interval = setInterval(() => {
      const elapsed = Date.now() - (startTime || 0);
      const remaining = Math.max(estimatedDuration - elapsed, 0);
      setTimeRemaining(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, startTime, estimatedDuration]);

  // Complete
  useEffect(() => {
    if (!isActive && progress > 0) {
      setProgress(100);
      setCurrentStep(steps.length - 1);
      onComplete?.();
    }
  }, [isActive, progress, onComplete, steps.length]);

  if (!isActive) return null;

  const formatTime = (ms: number) => {
    const seconds = Math.ceil(ms / 1000);
    if (seconds < 60) return `约 ${seconds} 秒`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `约 ${minutes} 分 ${secs} 秒`;
  };

  return (
    <Card className={cn('border-primary/20 bg-gradient-to-br from-primary/5 to-transparent', className)}>
      <CardContent className="pt-6">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="relative">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium">{title}</h3>
            <p className="text-sm text-muted-foreground">{steps[currentStep]}</p>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            {timeRemaining > 0 ? formatTime(timeRemaining) : '即将完成'}
          </div>
        </div>

        {/* Progress bar */}
        <Progress value={progress} className="h-2" />

        {/* Steps indicator */}
        <div className="mt-4 space-y-2">
          {steps.map((step, index) => (
            <div
              key={index}
              className={cn(
                'flex items-center gap-2 text-sm transition-all duration-300',
                index < currentStep ? 'text-green-600' : index === currentStep ? 'text-primary font-medium' : 'text-muted-foreground/50'
              )}
            >
              {index < currentStep ? (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              ) : index === currentStep ? (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
              ) : (
                <div className="h-4 w-4 shrink-0 rounded-full border-2 border-muted-foreground/20" />
              )}
              <span className="truncate">{step}</span>
            </div>
          ))}
        </div>

        {/* Footer tip */}
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
          <Sparkles className="h-3.5 w-3.5" />
          <span>AI 正在处理，此过程可能需要 30-60 秒，请耐心等待</span>
        </div>
      </CardContent>
    </Card>
  );
}

/** Simple loading overlay for full-page AI tasks */
export function AILoadingOverlay({
  isActive,
  title = 'AI 处理中',
  message = '正在分析案件数据，请稍候...',
}: {
  isActive: boolean;
  title?: string;
  message?: string;
}) {
  const [dots, setDots] = useState('');

  useEffect(() => {
    if (!isActive) return;
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);
    return () => clearInterval(interval);
  }, [isActive]);

  if (!isActive) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <Card className="w-full max-w-md border-primary/20 shadow-lg">
        <CardContent className="pt-8 pb-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {message}
            <span className="inline-block w-6 text-left">{dots}</span>
          </p>
          <Progress value={undefined} className="mt-4 h-1" />
        </CardContent>
      </Card>
    </div>
  );
}
