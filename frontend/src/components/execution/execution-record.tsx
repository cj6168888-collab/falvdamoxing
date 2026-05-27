import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Record { date: string; type: string; amount?: number; description: string; operator?: string; }
interface Props { records: Record[]; }

export function ExecutionRecordList({ records }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>执行记录</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {!records?.length ? <p className="text-muted-foreground text-center py-4">暂无记录</p> : records.map((r, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div>
              <p className="text-sm font-medium">{r.type}</p>
              <p className="text-xs text-muted-foreground">{formatChineseDate(r.date)}{r.amount != null ? ' · ¥' + r.amount.toLocaleString() : ''}</p>
              {r.description && <p className="text-xs text-muted-foreground">{r.description}</p>}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
