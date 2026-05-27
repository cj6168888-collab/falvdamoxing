import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Circle } from 'lucide-react';

const MILESTONES = ['递交上诉状', '缴纳上诉费', '提交答辩状', '二审开庭', '二审判决'];

interface Props { completedCount: number; }

export function AppealMilestone({ completedCount }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>上诉里程碑</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {MILESTONES.map((m, i) => (
          <div key={m} className="flex items-center gap-3">
            {i < completedCount ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
            <span className={i < completedCount ? 'text-green-600' : 'text-muted-foreground'}>{m}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
