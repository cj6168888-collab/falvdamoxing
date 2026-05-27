import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useEvidenceCompleteness } from '@/hooks/use-evidence';

interface Props { caseId: string; }

interface EvidenceCompletenessGap {
  type: string;
  suggestion: string;
}

export function CompletenessCheck({ caseId }: Props) {
  const { data, isLoading } = useEvidenceCompleteness(caseId);
  if (isLoading) return <div className="animate-pulse"><div className="h-4 w-full rounded bg-muted" /></div>;
  return (
    <Card>
      <CardHeader><CardTitle>证据完整性检查</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Progress value={data?.completeness || 0} />
        <p className="text-sm text-center">{data?.completeness || 0}% 完整</p>
        {data?.gaps?.map((g: EvidenceCompletenessGap, i: number) => (
          <div key={i} className="p-3 rounded-lg border">
            <p className="font-medium">{g.type}</p>
            <p className="text-sm text-muted-foreground">{g.suggestion}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
