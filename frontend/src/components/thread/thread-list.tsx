import { ListTodo } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { CaseThread } from '@/types/thread.types';

interface Props { threads: CaseThread[]; isLoading: boolean; onAdd: () => void; onSelect: (thread: CaseThread) => void; }

export function ThreadList({ threads, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-16 rounded bg-muted" /></div>;
  if (threads.length === 0) return (
    <div className="text-center py-8">
      <ListTodo className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-2 text-muted-foreground">暂无线索</p>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">线索 ({threads.length})</h3>
        <button onClick={onAdd} className="text-sm text-primary hover:underline">添加</button>
      </div>
      {threads.map((t) => (
        <Card key={t.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(t)}>
          <CardContent className="p-4"><p className="font-medium">{t.title}</p><p className="text-sm text-muted-foreground">{t.status} · {t.priority}</p></CardContent>
        </Card>
      ))}
    </div>
  );
}
