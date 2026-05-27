import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Circle } from 'lucide-react';

interface Task { title: string; completed: boolean; }
interface Props { tasks: Task[]; }

export function StageTaskList({ tasks }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>阶段任务</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {tasks.map((t, i) => (
          <div key={i} className="flex items-center gap-3">
            {t.completed ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
            <span className={t.completed ? 'text-green-600' : ''}>{t.title}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
