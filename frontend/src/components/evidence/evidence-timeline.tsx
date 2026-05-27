import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Item { name: string; createdAt: string; }
interface Props { evidence: Item[]; }

export function EvidenceTimeline({ evidence }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>证据时间轴</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {evidence.map((e, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div><p className="text-sm font-medium">{e.name}</p><p className="text-xs text-muted-foreground">{formatChineseDate(e.createdAt)}</p></div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
