import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import type { AppealArgument } from '@/types/appeal.types';

interface Props { arguments: AppealArgument[]; isLoading: boolean; onAdd: () => void; }

export function AppealArgumentList({ arguments: args, isLoading, onAdd }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-20 rounded bg-muted" /></div>;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">上诉论证</h3>
        <Button size="sm" onClick={onAdd}><Plus className="mr-2 h-4 w-4" />添加论证</Button>
      </div>
      {!args?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无论证点</p>
      ) : (
        <div className="space-y-3">
          {args.map((a) => (
            <Card key={a.id}>
              <CardContent className="p-4">
                <p className="font-medium">{a.title}</p>
                <p className="text-sm text-muted-foreground">{a.argument_type} · 成功率: {a.success_probability ?? 0}%</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
