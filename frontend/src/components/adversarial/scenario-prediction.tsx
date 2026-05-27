import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Scenario { scenario: string; probability: number; description: string; }
interface Props { scenarios: Scenario[]; }

export function ScenarioPrediction({ scenarios }: Props) {
  if (!scenarios?.length) return <p className="text-muted-foreground text-center py-8">暂无预测数据</p>;
  return (
    <Card>
      <CardHeader><CardTitle>情景预测</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {scenarios.map((s, i) => (
          <div key={i}>
            <div className="flex justify-between text-sm mb-1"><span>{s.scenario}</span><span>{s.probability}%</span></div>
            <Progress value={s.probability} />
            <p className="text-xs text-muted-foreground mt-1">{s.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
