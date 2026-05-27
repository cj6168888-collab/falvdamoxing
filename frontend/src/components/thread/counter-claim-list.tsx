import { Scale } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { CounterClaim } from '@/types/thread.types';

interface Props { claims: CounterClaim[]; isLoading: boolean; onAdd: () => void; onSelect: (claim: CounterClaim) => void; }

export function CounterClaimList({ claims, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-16 rounded bg-muted" /></div>;
  if (claims.length === 0) return (
    <div className="text-center py-8">
      <Scale className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-2 text-muted-foreground">暂无反诉</p>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">反诉/追加请求 ({claims.length})</h3>
        <button onClick={onAdd} className="text-sm text-primary hover:underline">添加</button>
      </div>
      {claims.map((c) => (
        <Card key={c.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(c)}>
          <CardContent className="p-4"><p className="font-medium">{c.title}</p><p className="text-sm text-muted-foreground">{c.status} {c.amount ? '· ¥' + c.amount.toLocaleString() : ''}</p></CardContent>
        </Card>
      ))}
    </div>
  );
}
