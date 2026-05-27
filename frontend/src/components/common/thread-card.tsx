import { Card, CardContent } from '@/components/ui/card';
import { ListTodo } from 'lucide-react';

interface Props { title: string; status: string; priority: string; onClick: () => void; }

export function ThreadCard({ title, status, priority, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <ListTodo className="h-4 w-4 text-muted-foreground" />
          <p className="font-medium">{title}</p>
        </div>
        <p className="text-sm text-muted-foreground mt-1">{status} · {priority}</p>
      </CardContent>
    </Card>
  );
}
