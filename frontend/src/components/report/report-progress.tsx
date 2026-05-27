import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Props { progress: number; currentSection?: string; }

export function ReportProgress({ progress, currentSection }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>生成进度</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Progress value={progress} />
        <p className="text-sm text-center">{progress}%</p>
        {currentSection && <p className="text-xs text-muted-foreground text-center">当前: {currentSection}</p>}
      </CardContent>
    </Card>
  );
}
