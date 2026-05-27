import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { caseId: string; }

export function KnowledgeGraph({ caseId: _caseId }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>知识图谱</CardTitle></CardHeader>
      <CardContent>
        <div className="h-[400px] flex items-center justify-center rounded-lg border bg-muted/20">
          <p className="text-muted-foreground">知识图谱可视化区域</p>
        </div>
      </CardContent>
    </Card>
  );
}
