import { Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface Props { version: number; timestamp: string; isCurrent?: boolean; onSelect: () => void; onCompare?: () => void; }

export function DocumentVersion({ version, timestamp, isCurrent, onSelect, onCompare }: Props) {
  return (
    <Card className={isCurrent ? 'border-primary' : 'cursor-pointer hover:shadow-md'} onClick={onSelect}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">v{version}</span>
          </div>
          {isCurrent && <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">当前</span>}
        </div>
        <p className="text-xs text-muted-foreground mt-2">{timestamp}</p>
        {onCompare && !isCurrent && <button onClick={(e) => { e.stopPropagation(); onCompare(); }} className="mt-2 text-xs text-primary hover:underline">对比当前版本</button>}
      </CardContent>
    </Card>
  );
}
