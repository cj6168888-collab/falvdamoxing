import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Interaction { action: string; timestamp: string; }
interface Props { interactions: Interaction[]; }

export function InteractionHistory({ interactions }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>交互历史</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {interactions.map((h, i) => (
          <div key={i} className="flex justify-between text-sm">
            <span>{h.action}</span>
            <span className="text-muted-foreground">{formatChineseDate(h.timestamp)}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
