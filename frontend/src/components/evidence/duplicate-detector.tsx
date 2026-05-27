import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy } from 'lucide-react';

interface Duplicate { id: string; name: string; similarity: number; }
interface Props { duplicates: Duplicate[] | null | undefined; onMerge: (ids: string[]) => void; }

export function DuplicateDetector({ duplicates, onMerge }: Props) {
  if (!duplicates?.length) return null;
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><Copy className="h-5 w-5 text-amber-500" />重复检测</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {duplicates.map((d) => (
          <div key={d.id} className="flex justify-between items-center p-3 rounded-lg border">
            <div><p className="font-medium">{d.name}</p><p className="text-sm text-muted-foreground">相似度: {d.similarity}%</p></div>
            <Button size="sm" variant="outline" onClick={() => onMerge([d.id])}>合并</Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
