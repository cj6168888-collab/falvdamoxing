import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Evidence { id: string; name: string; type: string; source: string; credibilityScore?: number; description?: string; }
interface Props { evidence: Evidence; }

export function EvidenceDetail({ evidence }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>{evidence.name}</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div><p className="text-sm text-muted-foreground">类型</p><p>{evidence.type}</p></div>
        <div><p className="text-sm text-muted-foreground">来源</p><p>{evidence.source}</p></div>
        {evidence.credibilityScore != null && <div><p className="text-sm text-muted-foreground">信度评分</p><p>{evidence.credibilityScore}%</p></div>}
        {evidence.description && <div><p className="text-sm text-muted-foreground">描述</p><p>{evidence.description}</p></div>}
      </CardContent>
    </Card>
  );
}
