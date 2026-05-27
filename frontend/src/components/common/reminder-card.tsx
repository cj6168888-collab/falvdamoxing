import { Bell } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';

interface Props { title: string; caseTitle: string; type: string; dueDate?: string; isRead: boolean; priority: 'high' | 'medium' | 'low'; onClick: () => void; onMarkRead: () => void; }

export function ReminderCard({ title, caseTitle, type: _type, dueDate, isRead, priority, onClick, onMarkRead }: Props) {
  const priorityColors: Record<string, string> = { high: 'border-l-red-500', medium: 'border-l-amber-500', low: 'border-l-green-500' };
  return (
    <div className={`rounded-lg border border-l-4 ${priorityColors[priority]} bg-card p-4 ${!isRead ? 'font-medium' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <span>{title}</span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{caseTitle}</p>
          {dueDate && <p className="mt-1 text-xs text-muted-foreground">截止: {formatChineseDate(dueDate)}</p>}
        </div>
        <div className="flex gap-2">
          <button onClick={onClick} className="text-sm text-primary hover:underline">查看</button>
          {!isRead && <button onClick={onMarkRead} className="text-sm text-muted-foreground hover:underline">标记已读</button>}
        </div>
      </div>
    </div>
  );
}
