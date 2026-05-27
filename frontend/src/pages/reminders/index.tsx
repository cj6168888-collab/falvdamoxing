import { useState } from 'react';
import { useReminders, useReminderStats, useMarkReminderRead, useMarkAllRemindersRead, useMarkReminderComplete, useDeleteReminder, useSnoozeReminder, useBatchUpdateReminders, useCreateReminder, useAutoGenerateAllReminders } from '@/api/reminder.api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Clock, Trash2, BellOff, Plus, CheckCircle2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import type { Reminder } from '@/types/reminder.types';

const TYPE_MAP: Record<string, string> = {
  deadline: '期限提醒',
  material_missing: '材料缺失',
  hearing: '开庭提醒',
  evidence: '证据提醒',
  risk: '风险预警',
  opportunity: '机会提示',
  strategy: '策略建议',
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'text-red-600 bg-red-50 dark:bg-red-900/20',
  medium: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20',
  low: 'text-green-600 bg-green-50 dark:bg-green-900/20',
};

function ReminderCard({ reminder, onMarkRead, onComplete, onDelete, onSnooze }: {
  reminder: Reminder;
  onMarkRead: () => void;
  onComplete: () => void;
  onDelete: () => void;
  onSnooze: () => void;
}) {
  const isOverdue = reminder.is_overdue || (reminder.days_until_trigger !== undefined && reminder.days_until_trigger < 0);
  const isUrgent = reminder.days_until_trigger !== undefined && reminder.days_until_trigger >= 0 && reminder.days_until_trigger <= 3;

  return (
    <Card className={`transition-colors ${reminder.is_completed ? 'opacity-60' : ''} ${isOverdue && !reminder.is_completed ? 'border-red-200 dark:border-red-800' : ''}`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <button onClick={onComplete} className="mt-1 flex-shrink-0">
            {reminder.is_completed ? <CheckCircle2 className="h-5 w-5 text-green-500" /> : <div className="h-5 w-5 rounded-full border-2 border-gray-300 hover:border-green-500" />}
          </button>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`font-medium ${reminder.is_completed ? 'line-through text-muted-foreground' : ''} ${!reminder.is_read ? 'text-foreground' : 'text-muted-foreground'}`}>
                {reminder.title}
              </span>
              <Badge className={`${PRIORITY_COLORS[reminder.priority] || ''} border-0`}>{reminder.priority === 'high' ? '高' : reminder.priority === 'medium' ? '中' : '低'}</Badge>
              {isOverdue && !reminder.is_completed && <Badge variant="destructive">已过期</Badge>}
              {isUrgent && !reminder.is_completed && <Badge variant="outline" className="text-amber-600">紧急</Badge>}
            </div>
            {reminder.content && <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{reminder.content}</p>}
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span>{TYPE_MAP[reminder.reminder_type] || reminder.reminder_type}</span>
              {reminder.case_title && <span>案件: {reminder.case_title}</span>}
              {reminder.trigger_date && <span>触发: {new Date(reminder.trigger_date).toLocaleDateString('zh-CN')}</span>}
              {reminder.days_until_trigger !== undefined && !reminder.is_completed && (
                <span className={isOverdue ? 'text-red-500' : isUrgent ? 'text-amber-500' : ''}>
                  {isOverdue ? `已过期 ${Math.abs(reminder.days_until_trigger)} 天` : `剩余 ${reminder.days_until_trigger} 天`}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            {!reminder.is_read && <Button variant="ghost" size="sm" onClick={onMarkRead} title="标记已读"><BellOff className="h-4 w-4" /></Button>}
            <Button variant="ghost" size="sm" onClick={onSnooze} title="延后1天"><Clock className="h-4 w-4" /></Button>
            <Button variant="ghost" size="sm" onClick={onDelete} title="删除"><Trash2 className="h-4 w-4" /></Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function RemindersPage() {
  const [filter, setFilter] = useState<'all' | 'unread' | 'uncompleted' | 'overdue'>('all');
  const [createDialog, setCreateDialog] = useState(false);
  const [createForm, setCreateForm] = useState<Partial<Reminder>>({ priority: 'medium', reminder_type: 'deadline' });

  const { data: remindersData, isLoading } = useReminders();
  const { data: stats } = useReminderStats();

  const markRead = useMarkReminderRead();
  const markAllRead = useMarkAllRemindersRead();
  const markComplete = useMarkReminderComplete();
  const deleteReminder = useDeleteReminder();
  const snoozeReminder = useSnoozeReminder();
  const batchUpdate = useBatchUpdateReminders();
  const createReminder = useCreateReminder();
  const autoGenerateAll = useAutoGenerateAllReminders();

  const handleAutoGenerateAll = () => {
    autoGenerateAll.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(data.message || `已生成 ${data.total || 0} 条提醒`);
      },
      onError: () => {
        toast.error('批量生成提醒失败');
      },
    });
  };

  const reminders = remindersData?.reminders || [];

  const filteredReminders = reminders.filter((r) => {
    if (filter === 'unread') return !r.is_read && !r.is_completed;
    if (filter === 'uncompleted') return !r.is_completed;
    if (filter === 'overdue') return r.is_overdue && !r.is_completed;
    return true;
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">提醒中心</h1>
          <p className="text-sm text-muted-foreground mt-1">管理所有案件提醒和待办事项</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={createDialog} onOpenChange={setCreateDialog}>
            <DialogTrigger asChild><Button variant="outline" size="sm"><Plus className="mr-1 h-3 w-3" />新建提醒</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>新建提醒</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2"><Label>标题</Label><Input value={createForm.title || ''} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} /></div>
                <div className="space-y-2"><Label>内容</Label><Textarea value={createForm.content || ''} onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })} rows={3} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>类型</Label>
                    <Select value={createForm.reminder_type} onValueChange={(v) => setCreateForm({ ...createForm, reminder_type: v as Reminder['reminder_type'] })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {Object.entries(TYPE_MAP).map(([k, v]) => (<SelectItem key={k} value={k}>{v}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2"><Label>优先级</Label>
                    <Select value={createForm.priority} onValueChange={(v) => setCreateForm({ ...createForm, priority: v as Reminder['priority'] })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="high">高</SelectItem><SelectItem value="medium">中</SelectItem><SelectItem value="low">低</SelectItem></SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2"><Label>触发日期</Label><Input type="datetime-local" value={createForm.trigger_date || ''} onChange={(e) => setCreateForm({ ...createForm, trigger_date: e.target.value })} /></div>
                <Button onClick={async () => { if (!createForm.title || !createForm.content) return; await createReminder.mutateAsync(createForm); setCreateDialog(false); setCreateForm({ priority: 'medium', reminder_type: 'deadline' }); }} disabled={createReminder.isPending} className="w-full">{createReminder.isPending ? '创建中...' : '创建提醒'}</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.total}</div><p className="text-xs text-muted-foreground">总提醒</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-amber-500">{stats.unread}</div><p className="text-xs text-muted-foreground">未读</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-red-500">{stats.overdue}</div><p className="text-xs text-muted-foreground">已过期</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-green-500">{stats.completed}</div><p className="text-xs text-muted-foreground">已完成</p></CardContent></Card>
        </div>
      )}

      <div className="flex items-center gap-2">
        <Tabs value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
          <TabsList>
            <TabsTrigger value="all">全部</TabsTrigger>
            <TabsTrigger value="unread">未读</TabsTrigger>
            <TabsTrigger value="uncompleted">未完成</TabsTrigger>
            <TabsTrigger value="overdue">已过期</TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="ml-auto flex gap-2">
          <Button variant="outline" size="sm" onClick={handleAutoGenerateAll} disabled={autoGenerateAll.isPending}>
            <Sparkles className="mr-1 h-3 w-3" />
            {autoGenerateAll.isPending ? '生成中...' : '智能生成'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => markAllRead.mutate(undefined)} disabled={!stats?.unread}>全部已读</Button>
          <Button variant="outline" size="sm" onClick={() => {
            const uncompletedIds = reminders.filter(r => !r.is_completed).map(r => r.id);
            if (uncompletedIds.length) batchUpdate.mutate({ reminder_ids: uncompletedIds, is_completed: true });
          }}>批量完成</Button>
        </div>
      </div>

      {!filteredReminders.length ? (
        <EmptyState title="暂无提醒" description="所有事项已处理完毕" />
      ) : (
        <div className="space-y-3">
          {filteredReminders.map((reminder) => (
            <ReminderCard
              key={reminder.id}
              reminder={reminder}
              onMarkRead={() => markRead.mutate(reminder.id)}
              onComplete={() => markComplete.mutate(reminder.id)}
              onDelete={() => deleteReminder.mutate(reminder.id)}
              onSnooze={() => snoozeReminder.mutate({ reminderId: reminder.id, days: 1 })}
            />
          ))}
        </div>
      )}
    </div>
  );
}
