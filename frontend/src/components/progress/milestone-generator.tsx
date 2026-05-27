import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useGenerateMilestones } from '@/hooks/use-deadline';

interface Props { caseId: string; }

export function MilestoneGenerator({ caseId }: Props) {
  const generate = useGenerateMilestones();
  return (
    <Card>
      <CardHeader><CardTitle>AI 生成里程碑</CardTitle></CardHeader>
      <CardContent><Button onClick={() => generate.mutate(caseId)} disabled={generate.isPending}>{generate.isPending ? '生成中...' : '生成里程碑'}</Button></CardContent>
    </Card>
  );
}
