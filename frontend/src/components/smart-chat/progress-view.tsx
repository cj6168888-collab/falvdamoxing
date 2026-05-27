import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Loader2, Check, Shield } from 'lucide-react';

interface ProgressViewProps {
  step: number;
  progress: number;
  evidenceCount: number;
  steps?: string[];
}

const DEFAULT_STEPS = [
  '正在读取案件完整档案...',
  '正在逐一分析全部证据...',
  '正在建立证据关联网络...',
  '正在分析可主张的权利...',
  '正在计算建议金额...',
  '正在评估风险与底线...',
  '正在生成分析报告...',
];

export function ProgressView({ step, progress, evidenceCount, steps = DEFAULT_STEPS }: ProgressViewProps) {
  return (
    <div className="mx-auto max-w-2xl py-12 px-4">
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            AI 正在分析案情
          </CardTitle>
          <CardDescription>基于案件全部证据进行深度分析</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={progress} className="h-2" />
          <div className="space-y-2">
            {steps.map((s, i) => (
              <div key={i} className={`flex items-center gap-2 text-sm ${i < step ? 'text-green-600' : i === step ? 'text-primary font-medium' : 'text-muted-foreground/50'}`}>
                {i < step ? <Check className="h-4 w-4" /> : i === step ? <Loader2 className="h-4 w-4 animate-spin" /> : <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/20" />}
                {s}
              </div>
            ))}
          </div>
          <div className="rounded-lg bg-muted/50 px-3 py-2 text-xs text-muted-foreground flex items-center gap-2">
            <Shield className="h-3.5 w-3.5" />
            AI 正在阅读全部 {evidenceCount} 份证据，请稍候...
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
