import { Clock } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';

interface DeadlineCountdownProps {
  dueDate: string;
  daysRemaining: number;
}

export function DeadlineCountdown({ dueDate, daysRemaining }: DeadlineCountdownProps) {
  const isExpired = daysRemaining < 0;
  const isUrgent = daysRemaining >= 0 && daysRemaining <= 3;
  const isWarning = daysRemaining > 3 && daysRemaining <= 7;

  return (
    <div className={`flex items-center gap-2 rounded-md px-2 py-1 text-xs ${isExpired ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : isUrgent ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' : isWarning ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'}`}>
      <Clock className="h-3 w-3" />
      <span>{isExpired ? `已过期 ${Math.abs(daysRemaining)} 天` : daysRemaining === 0 ? '今天到期' : `还剩 ${daysRemaining} 天`}</span>
      <span className="text-muted-foreground">({formatChineseDate(dueDate)})</span>
    </div>
  );
}
