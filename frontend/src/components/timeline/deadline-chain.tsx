import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Event { date: string; title: string; type: string; }
interface Props { events: Event[]; }

export function DeadlineChain({ events }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>期限链</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div><p className="text-sm font-medium">{e.title}</p><p className="text-xs text-muted-foreground">{formatChineseDate(e.date)} · {e.type}</p></div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
