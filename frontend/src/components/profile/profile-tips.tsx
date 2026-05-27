import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb } from 'lucide-react';

interface Props {
  tips: string[];
}

export function ProfileTips({ tips }: Props) {
  if (!tips || tips.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Lightbulb className="h-4 w-4 text-yellow-500" />
          智能建议
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {tips.map((tip, i) => (
            <div key={i} className="flex items-start gap-2 rounded-lg bg-muted/50 p-3 text-sm">
              <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-yellow-500" />
              <span>{tip}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
