import { Card, CardContent } from '@/components/ui/card';
import { AlertTriangle } from 'lucide-react';

interface Props { deadline: string; daysRemaining: number; }

export function AppealCountdown({ deadline, daysRemaining }: Props) {
  const isUrgent = daysRemaining <= 7;
  return (
    <Card className={isUrgent ? 'border-red-500' : ''}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          {isUrgent && <AlertTriangle className="h-5 w-5 text-red-500" />}
          <div>
            <p className="text-sm text-muted-foreground">上诉期限</p>
            <p className="text-2xl font-bold">{daysRemaining} 天</p>
            <p className="text-xs text-muted-foreground">{deadline}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
