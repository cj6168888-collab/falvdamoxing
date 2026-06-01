import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Scenario { scenario: string; probability: number; description: string; }
interface Props { scenarios: Scenario[]; }

const scenarioLabelMap: Record<string, string> = {
  胜诉: '我方主张获较高支持',
  部分胜诉: '我方主张获部分支持',
  败诉: '我方主张未获支持',
};

function getReviewableScenarioLabel(scenario: string) {
  return scenarioLabelMap[scenario] || scenario;
}

export function ScenarioPrediction({ scenarios }: Props) {
  if (!scenarios?.length) return <p className="text-muted-foreground text-center py-8">暂无情景参考数据</p>;
  return (
    <Card>
      <CardHeader>
        <CardTitle>裁判支持度参考</CardTitle>
        <CardDescription>仅作为诉讼风险工作底稿，需结合证据、管辖法院规则与律师复核。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {scenarios.map((s, i) => (
          <div key={i}>
            <div className="flex justify-between gap-3 text-sm mb-1">
              <span>{getReviewableScenarioLabel(s.scenario)}</span>
              <span className="shrink-0">支持度参考 {s.probability}%</span>
            </div>
            <Progress value={s.probability} />
            <p className="text-xs text-muted-foreground mt-1">{s.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
