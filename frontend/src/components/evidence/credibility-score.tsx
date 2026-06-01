import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Dimension { name: string; score: number; }
interface Props { score: number; dimensions: Dimension[]; }

export function CredibilityScore({ score, dimensions }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>证明力参考</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs text-muted-foreground">
          仅作工作底稿中的证据风险参考，不等同于法院采信结论。
        </p>
        <div className="text-center"><p className="text-3xl font-bold">{score}%</p><Progress value={score} className="mt-2" /></div>
        <div className="space-y-2">
          {dimensions.map((d, i) => (
            <div key={i}>
              <div className="flex justify-between text-sm"><span>{d.name}</span><span>{d.score}%</span></div>
              <Progress value={d.score} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
