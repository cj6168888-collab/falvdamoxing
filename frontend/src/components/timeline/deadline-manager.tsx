import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useDeadlineList } from '@/hooks/use-deadline';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';

interface Props { caseId: string; }

interface DeadlineListItem {
  id: string | number;
  title?: string;
  dueDate?: string | Date;
}

export function DeadlineManager({ caseId }: Props) {
  const { data, isLoading } = useDeadlineList(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">截止日期管理</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />添加截止日</Button>
      </div>
      {!data?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无截止日期</p>
      ) : (
        <div className="space-y-3">
          {data.map((d: DeadlineListItem) => (
            <Card key={d.id}><CardContent className="p-4"><div className="flex justify-between items-center"><div><p className="font-medium">{d.title}</p><p className="text-sm text-muted-foreground">{d.dueDate ? formatChineseDate(d.dueDate) : '未设置'}</p></div></div></CardContent></Card>
          ))}
        </div>
      )}
    </div>
  );
}
