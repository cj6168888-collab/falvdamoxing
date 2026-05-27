import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';

interface Deadline { title: string; dueDate: string; daysRemaining: number; }
interface Props { deadlines: Deadline[]; }

export function UrgencyReport({ deadlines }: Props) {
  const urgent = deadlines.filter((d) => d.daysRemaining <= 7).sort((a, b) => a.daysRemaining - b.daysRemaining);
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" />紧迫度报告</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {urgent.map((d, i) => (
          <div key={i} className="flex justify-between items-center">
            <div><p className="font-medium">{d.title}</p><p className="text-xs text-muted-foreground">{formatChineseDate(d.dueDate)}</p></div>
            <span className="text-sm font-medium text-red-600">{d.daysRemaining} 天</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
