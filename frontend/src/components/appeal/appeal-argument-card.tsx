import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Props { title: string; type: string; successProbability?: number; }

export function AppealArgumentCard({ title, type, successProbability }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="font-medium">{title}</p>
        <p className="text-sm text-muted-foreground">{type}</p>
        {successProbability != null && (
          <div className="mt-2">
            <Progress value={successProbability} />
            <p className="text-xs text-muted-foreground mt-1">成功率: {successProbability}%</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
