import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Circle } from 'lucide-react';

interface Props { actions: string[]; onAction: (action: string) => void; }

export function ActionPlan({ actions, onAction }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>行动计划</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {actions.map((a, i) => (
          <div key={i} className="flex items-center gap-3">
            <Circle className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm flex-1">{a}</span>
            <Button size="sm" variant="outline" onClick={() => onAction(a)}>执行</Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
