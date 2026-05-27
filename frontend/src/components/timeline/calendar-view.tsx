import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { format, startOfMonth, endOfMonth, eachDayOfInterval } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface Props { deadlines: { date: string; title: string }[]; }

export function CalendarView({ deadlines: _deadlines }: Props) {
  const now = new Date();
  const days = eachDayOfInterval({ start: startOfMonth(now), end: endOfMonth(now) });
  return (
    <Card>
      <CardHeader><CardTitle>{format(now, 'yyyy 年 M 月', { locale: zhCN })}</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-1 text-center text-sm">
          <span className="font-medium">日</span><span className="font-medium">一</span><span className="font-medium">二</span><span className="font-medium">三</span><span className="font-medium">四</span><span className="font-medium">五</span><span className="font-medium">六</span>
          {days.map((d, i) => (
            <div key={i} className={`p-2 rounded ${format(d, 'yyyy-MM-dd') === format(now, 'yyyy-MM-dd') ? 'bg-primary text-primary-foreground' : ''}`}>
              <span>{format(d, 'd')}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
