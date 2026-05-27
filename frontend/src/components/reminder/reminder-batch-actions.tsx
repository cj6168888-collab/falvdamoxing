import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Trash2,
  Bell,
  BellOff,
  CheckCircle2,
  Clock,
  Loader2,
  ChevronDown,
} from 'lucide-react';
import type { Reminder } from '@/types/reminder.types';

interface BatchActionsToolbarProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onBatchMarkRead: () => void;
  onBatchMarkUnread: () => void;
  onBatchComplete: () => void;
  onBatchUncomplete: () => void;
  onBatchSnooze: (days: number) => void;
  onBatchDelete: () => void;
  isLoading?: boolean;
}

export function BatchActionsToolbar({
  selectedCount,
  totalCount,
  onSelectAll,
  onDeselectAll,
  onBatchMarkRead,
  onBatchMarkUnread,
  onBatchComplete,
  onBatchUncomplete,
  onBatchSnooze,
  onBatchDelete,
  isLoading = false,
}: BatchActionsToolbarProps) {
  const [snoozeDialogOpen, setSnoozeDialogOpen] = useState(false);
  const [snoozeDays, setSnoozeDays] = useState(1);

  const handleSnooze = () => {
    onBatchSnooze(snoozeDays);
    setSnoozeDialogOpen(false);
  };

  return (
    <>
      <Card className="border-primary/50 bg-primary/5">
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            {/* 选择状态 */}
            <div className="flex items-center gap-3">
              <Checkbox
                checked={selectedCount === totalCount && totalCount > 0}
                ref={(el) => {
                  if (el) {
                    (el as unknown as { indeterminate: boolean }).indeterminate =
                      selectedCount > 0 && selectedCount < totalCount;
                  }
                }}
                onCheckedChange={(checked) => (checked ? onSelectAll() : onDeselectAll())}
                aria-label="全选"
              />
              <Label
                className="cursor-pointer"
                onClick={() => (selectedCount === totalCount ? onDeselectAll() : onSelectAll())}
              >
                已选择 <span className="font-bold text-primary">{selectedCount}</span> / {totalCount} 项
              </Label>
            </div>

            {/* 操作按钮 */}
            {selectedCount > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                {/* 标记已读/未读 */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBatchMarkRead}
                  disabled={isLoading}
                  className="gap-1"
                >
                  <BellOff className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">已读</span>
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBatchMarkUnread}
                  disabled={isLoading}
                  className="gap-1"
                >
                  <Bell className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">未读</span>
                </Button>

                {/* 完成/取消完成 */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBatchComplete}
                  disabled={isLoading}
                  className="gap-1"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">完成</span>
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBatchUncomplete}
                  disabled={isLoading}
                  className="gap-1"
                >
                  <Clock className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">取消完成</span>
                </Button>

                {/* 延后菜单 */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" disabled={isLoading} className="gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      延后
                      <ChevronDown className="h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => { setSnoozeDays(1); setSnoozeDialogOpen(true); }}>
                      延后 1 天
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setSnoozeDays(3); setSnoozeDialogOpen(true); }}>
                      延后 3 天
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setSnoozeDays(7); setSnoozeDialogOpen(true); }}>
                      延后 1 周
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setSnoozeDays(30); setSnoozeDialogOpen(true); }}>
                      延后 1 个月
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => { setSnoozeDays(0); setSnoozeDialogOpen(true); }}>
                      自定义...
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* 删除 */}
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={onBatchDelete}
                  disabled={isLoading}
                  className="gap-1"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">删除</span>
                </Button>
              </div>
            )}

            {/* 加载状态 */}
            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">处理中...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 延后对话框 */}
      <Dialog open={snoozeDialogOpen} onOpenChange={setSnoozeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>延后提醒</DialogTitle>
            <DialogDescription>
              将选中的 {selectedCount} 条提醒延后
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="snooze-days">延后天数</Label>
              <div className="flex items-center gap-2">
                <input
                  id="snooze-days"
                  type="number"
                  min="0"
                  max="365"
                  value={snoozeDays}
                  onChange={(e) => setSnoozeDays(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-24 px-3 py-2 border rounded-md"
                />
                <span className="text-muted-foreground">天</span>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSnoozeDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSnooze}>确认延后</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// 确认删除对话框
interface ConfirmDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  count: number;
  onConfirm: () => void;
  isLoading?: boolean;
}

export function ConfirmDeleteDialog({
  open,
  onOpenChange,
  count,
  onConfirm,
  isLoading = false,
}: ConfirmDeleteDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认批量删除</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除选中的 {count} 条提醒吗？此操作不可撤销。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isLoading}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                删除中...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                确认删除
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// 提醒卡片（带复选框）
interface SelectableReminderCardProps {
  reminder: Reminder;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onMarkRead: () => void;
  onComplete: () => void;
  onDelete: () => void;
  onSnooze: () => void;
}

export function SelectableReminderCard({
  reminder,
  isSelected,
  onSelect,
  onMarkRead,
  onComplete,
  onDelete,
  onSnooze,
}: SelectableReminderCardProps) {
  const isOverdue = reminder.is_overdue || (reminder.days_until_trigger !== undefined && reminder.days_until_trigger < 0);
  const isUrgent =
    reminder.days_until_trigger !== undefined &&
    reminder.days_until_trigger >= 0 &&
    reminder.days_until_trigger <= 3;

  const PRIORITY_COLORS: Record<string, string> = {
    high: 'text-red-600 bg-red-50 dark:bg-red-900/20',
    medium: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20',
    low: 'text-green-600 bg-green-50 dark:bg-green-900/20',
  };

  const TYPE_MAP: Record<string, string> = {
    deadline: '期限提醒',
    material_missing: '材料缺失',
    hearing: '开庭提醒',
    evidence: '证据提醒',
    risk: '风险预警',
    opportunity: '机会提示',
    strategy: '策略建议',
  };

  return (
    <Card
      className={`transition-all cursor-pointer ${
        isSelected
          ? 'border-primary bg-primary/5 ring-1 ring-primary'
          : isOverdue && !reminder.is_completed
          ? 'border-red-200'
          : ''
      } ${reminder.is_completed ? 'opacity-60' : ''}`}
      onClick={() => onSelect(!isSelected)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Checkbox
            checked={isSelected}
            onCheckedChange={(checked) => onSelect(checked === true)}
            onClick={(e) => e.stopPropagation()}
            className="mt-1"
            aria-label={`选择提醒 ${reminder.title}`}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`font-medium ${
                  reminder.is_completed
                    ? 'line-through text-muted-foreground'
                    : !reminder.is_read
                    ? 'text-foreground'
                    : 'text-muted-foreground'
                }`}
              >
                {reminder.title}
              </span>
              <Badge className={`${PRIORITY_COLORS[reminder.priority] || ''} border-0`}>
                {reminder.priority === 'high' ? '高' : reminder.priority === 'medium' ? '中' : '低'}
              </Badge>
              {isOverdue && !reminder.is_completed && <Badge variant="destructive">已过期</Badge>}
              {isUrgent && !reminder.is_completed && (
                <Badge variant="outline" className="text-amber-600">
                  紧急
                </Badge>
              )}
            </div>
            {reminder.content && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {reminder.content}
              </p>
            )}
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span>{TYPE_MAP[reminder.reminder_type] || reminder.reminder_type}</span>
              {reminder.case_title && <span>案件: {reminder.case_title}</span>}
              {reminder.trigger_date && (
                <span>
                  触发: {new Date(reminder.trigger_date).toLocaleDateString('zh-CN')}
                </span>
              )}
              {reminder.days_until_trigger !== undefined && !reminder.is_completed && (
                <span
                  className={
                    isOverdue ? 'text-red-500' : isUrgent ? 'text-amber-500' : ''
                  }
                >
                  {isOverdue
                    ? `已过期 ${Math.abs(reminder.days_until_trigger)} 天`
                    : `剩余 ${reminder.days_until_trigger} 天`}
                </span>
              )}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {!reminder.is_read && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(event) => {
                    event.stopPropagation();
                    onMarkRead();
                  }}
                >
                  标记已读
                </Button>
              )}
              {!reminder.is_completed && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(event) => {
                    event.stopPropagation();
                    onComplete();
                  }}
                >
                  完成
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={(event) => {
                  event.stopPropagation();
                  onSnooze();
                }}
              >
                延后
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive hover:text-destructive"
                onClick={(event) => {
                  event.stopPropagation();
                  onDelete();
                }}
              >
                删除
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

