import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Props { totalAmount: number; executedAmount: number; }

export function ExecutionProgress({ totalAmount, executedAmount }: Props) {
  const progress = totalAmount ? Math.round((executedAmount / totalAmount) * 100) : 0;
  return (
    <Card>
      <CardHeader><CardTitle>执行进度</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Progress value={progress} />
        <div className="grid grid-cols-3 gap-4 text-center">
          <div><p className="text-sm text-muted-foreground">执行总额</p><p className="text-lg font-bold">¥{totalAmount?.toLocaleString()}</p></div>
          <div><p className="text-sm text-muted-foreground">已执行</p><p className="text-lg font-bold text-green-600">¥{executedAmount?.toLocaleString()}</p></div>
          <div><p className="text-sm text-muted-foreground">剩余</p><p className="text-lg font-bold text-red-600">¥{(totalAmount - executedAmount)?.toLocaleString()}</p></div>
        </div>
      </CardContent>
    </Card>
  );
}
