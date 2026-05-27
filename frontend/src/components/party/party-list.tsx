import { Users } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Party } from '@/types/party.types';

interface Props { parties: Party[]; isLoading: boolean; onAdd: () => void; onSelect: (party: Party) => void; }

export function PartyList({ parties, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-16 rounded bg-muted" /><div className="h-16 rounded bg-muted" /></div>;
  if (parties.length === 0) return (
    <div className="text-center py-8">
      <Users className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-2 text-muted-foreground">暂无当事人</p>
      <Button onClick={onAdd} className="mt-4">添加当事人</Button>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">当事人 ({parties.length})</h3>
        <Button size="sm" onClick={onAdd}>添加</Button>
      </div>
      {parties.map((p) => (
        <Card key={p.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(p)}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="font-medium">{p.name}</p><p className="text-sm text-muted-foreground">{p.role} · {p.phone || '无电话'}</p></div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
