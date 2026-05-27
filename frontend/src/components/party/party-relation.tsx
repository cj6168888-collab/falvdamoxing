import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Party { id: string; name: string; role: string; }
interface Relation { from: string; to: string; label: string; }
interface Props { parties: Party[]; relations: Relation[]; }

export function PartyRelation({ parties: _parties, relations: _relations }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>当事人关系图</CardTitle></CardHeader>
      <CardContent>
        <div className="h-[400px] flex items-center justify-center rounded-lg border bg-muted/20">
          <p className="text-muted-foreground">当事人关系可视化区域</p>
        </div>
      </CardContent>
    </Card>
  );
}
