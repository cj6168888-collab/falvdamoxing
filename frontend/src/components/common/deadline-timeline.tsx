import { Card, CardContent } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Props { events: { date: string; title: string; type: string }[]; }

export function DeadlineTimeline({ events }: Props) {
  return (
    <Card>
      <CardContent className="p-4 space-y-3">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div>
              <p className="text-sm font-medium">{e.title}</p>
              <p className="text-xs text-muted-foreground">{formatChineseDate(e.date)} · {e.type}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
