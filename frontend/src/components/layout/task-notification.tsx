import { Bell, CheckCircle2, XCircle, Loader2, ExternalLink } from 'lucide-react';
import { useTaskStore } from '@/stores/task.store';
import type { AITask } from '@/stores/task.store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

export function TaskNotification() {
  const activeTasks = useTaskStore((s) => s.getActiveTasks());
  const completedTasks = useTaskStore((s) => s.getCompletedTasks());
  const clearCompleted = useTaskStore((s) => s.clearCompleted);
  const navigate = useNavigate();

  const hasActive = activeTasks.length > 0;
  const hasCompleted = completedTasks.length > 0;
  const total = activeTasks.length + completedTasks.length;

  const formatTime = (ts: number) => {
    const diff = Date.now() - ts;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  const handleTaskClick = (task: AITask) => {
    if (task.status === 'completed' && task.result) {
      // Navigate to the relevant page based on task type
      const routeMap: Record<string, string> = {
        document_generate: `/cases/${task.caseId}/documents`,
        senior_analysis: `/senior-analysis/${task.caseId}`,
        report_generate: `/cases/${task.caseId}/reports`,
        adversarial: `/adversarial/${task.caseId}`,
      };
      const route = routeMap[task.type];
      if (route) navigate(route);
    }
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {total > 0 && (
            <Badge
              className={cn(
                'absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs flex items-center justify-center',
                hasActive ? 'bg-primary' : 'bg-muted-foreground'
              )}
            >
              {total}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="end">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h4 className="font-medium">AI 任务</h4>
          {hasCompleted && (
            <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={clearCompleted}>
              清除已完成
            </Button>
          )}
        </div>
        <div className="max-h-96 overflow-y-auto">
          {total === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">暂无任务</div>
          ) : (
            <div className="divide-y">
              {activeTasks.map((task) => (
                <div key={task.id} className="px-4 py-3">
                  <div className="flex items-start gap-3">
                    <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-primary shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{task.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{task.message}</p>
                      <div className="mt-1.5 h-1 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all duration-500"
                          style={{ width: `${Math.round(task.progress * 100)}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatTime(task.createdAt)} · {Math.round(task.progress * 100)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {completedTasks.map((task) => (
                <div
                  key={task.id}
                  className="px-4 py-3 cursor-pointer hover:bg-muted/50"
                  onClick={() => handleTaskClick(task)}
                >
                  <div className="flex items-start gap-3">
                    {task.status === 'completed' ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-500 shrink-0" />
                    ) : (
                      <XCircle className="mt-0.5 h-4 w-4 text-red-500 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1">
                        <p className="text-sm font-medium truncate">{task.title}</p>
                        <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0" />
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{task.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatTime(task.createdAt)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
