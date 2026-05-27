import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Annotation { text: string; page: number; }
interface Props { evidenceId: string; annotations: Annotation[]; }

export function EvidenceAnnotation({ evidenceId: _evidenceId, annotations }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>批注</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {annotations.map((a, i) => (
          <div key={i} className="p-2 rounded bg-muted">
            <p className="text-sm">{a.text}</p>
            <p className="text-xs text-muted-foreground">第 {a.page} 页</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
