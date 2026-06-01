import { Badge } from '@/components/ui/badge';

interface Props { intent: string; confidence: number; }

export function IntentDisplay({ intent, confidence }: Props) {
  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline">意图: {intent}</Badge>
      <span className="text-xs text-muted-foreground">识别参考 {Math.round(confidence * 100)}%</span>
    </div>
  );
}
