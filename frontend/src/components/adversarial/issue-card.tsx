import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Issue } from '@/types/issue.types';

interface Props { issue: Issue; onClick: () => void; }

export function IssueCard({ issue, onClick }: Props) {
  const priorityColors: Record<string, string> = { high: 'destructive', medium: 'default', low: 'secondary' };
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-base">{issue.title}</CardTitle>
          <Badge variant={(priorityColors[issue.priority] || 'secondary') as 'default'}>{issue.priority}</Badge>
        </div>
      </CardHeader>
      <CardContent><p className="text-sm text-muted-foreground line-clamp-2">{issue.ourPosition}</p></CardContent>
    </Card>
  );
}
