import { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useLocalStorage } from '@/hooks/use-local-storage';
import {
  ChevronUp,
  ChevronDown,
  Plus,
  Clock,
  Settings,
  GripVertical,
} from 'lucide-react';

// Quick Action Types
export type QuickActionType = 
  | 'case' 
  | 'document' 
  | 'calendar' 
  | 'chat' 
  | 'evidence' 
  | 'reminder';

export interface QuickAction {
  id: string;
  type: QuickActionType;
  label: string;
  icon: string;
  shortcut?: string;
  action: () => void;
  badge?: string;
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
}

export interface QuickPanelConfig {
  collapsed: boolean;
  position: 'bottom' | 'left' | 'right';
  visibleActions: string[];
  customActions: QuickAction[];
}

// Default Quick Actions
const DEFAULT_QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'new-case',
    type: 'case',
    label: '新建案件',
    icon: '📁',
    shortcut: 'Ctrl+N',
    action: () => console.log('New case'),
  },
  {
    id: 'new-document',
    type: 'document',
    label: '生成文书',
    icon: '📝',
    shortcut: 'Ctrl+D',
    action: () => console.log('New document'),
  },
  {
    id: 'calendar',
    type: 'calendar',
    label: '日程',
    icon: '📅',
    badge: '3',
    action: () => console.log('Calendar'),
  },
  {
    id: 'chat',
    type: 'chat',
    label: '对话助手',
    icon: '💬',
    badge: '2',
    action: () => console.log('Chat'),
  },
  {
    id: 'evidence',
    type: 'evidence',
    label: '证据缺口',
    icon: '🔍',
    badge: '5',
    badgeVariant: 'destructive',
    action: () => console.log('Evidence gaps'),
  },
  {
    id: 'reminder',
    type: 'reminder',
    label: '提醒',
    icon: '🔔',
    badge: '8',
    badgeVariant: 'secondary',
    action: () => console.log('Reminders'),
  },
];

// Quick Panel Component
interface QuickPanelProps {
  actions?: QuickAction[];
  onActionClick?: (action: QuickAction) => void;
  onCustomize?: () => void;
  storageKey?: string;
}

export function QuickPanel({
  actions = DEFAULT_QUICK_ACTIONS,
  onActionClick,
  onCustomize,
  storageKey = 'quick-panel-config',
}: QuickPanelProps) {
  const [config, setConfig] = useLocalStorage<QuickPanelConfig>(storageKey, {
    collapsed: false,
    position: 'bottom',
    visibleActions: actions.map(a => a.id),
    customActions: [],
  });

  const [expanded, setExpanded] = useState(!config.collapsed);

  const visibleActions = actions.filter(a => 
    config.visibleActions.includes(a.id)
  );

  const handleToggle = useCallback(() => {
    setExpanded(!expanded);
    setConfig({ ...config, collapsed: expanded });
  }, [expanded, config, setConfig]);

  const handleAction = useCallback((action: QuickAction) => {
    action.action();
    onActionClick?.(action);
  }, [onActionClick]);

  if (expanded) {
    return (
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t shadow-lg z-50">
        <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {new Date().toLocaleDateString('zh-CN', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {onCustomize && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={onCustomize}>
                    <Settings className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>自定义快捷面板</TooltipContent>
              </Tooltip>
            )}
            <Button variant="ghost" size="icon" onClick={handleToggle}>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-1 px-4 py-3 overflow-x-auto">
          {visibleActions.map((action) => (
            <Tooltip key={action.id}>
              <TooltipTrigger asChild>
                <button
                  onClick={() => handleAction(action)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border bg-background hover:bg-muted/50 transition-colors min-w-fit"
                >
                  <span className="text-xl">{action.icon}</span>
                  <span className="text-sm font-medium">{action.label}</span>
                  {action.badge && (
                    <Badge 
                      variant={action.badgeVariant || 'default'}
                      className="ml-1"
                    >
                      {action.badge}
                    </Badge>
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent>
                {action.label}
                {action.shortcut && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    {action.shortcut}
                  </span>
                )}
              </TooltipContent>
            </Tooltip>
          ))}

          <Separator orientation="vertical" className="h-8" />

          {/* Quick Add */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" className="flex-shrink-0">
                <Plus className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>添加快捷操作</TooltipContent>
          </Tooltip>
        </div>
      </div>
    );
  }

  // Collapsed state
  return (
    <div 
      className="fixed bottom-0 left-1/2 -translate-x-1/2 bg-background border shadow-lg rounded-t-lg z-50 cursor-pointer"
      onClick={handleToggle}
    >
      <div className="flex items-center gap-2 px-4 py-2">
        <GripVertical className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">快捷工具</span>
        <Badge variant="secondary" className="ml-1">{visibleActions.length}</Badge>
        <ChevronUp className="h-4 w-4 text-muted-foreground ml-2" />
      </div>
    </div>
  );
}

// Evidence Gap History Component
interface EvidenceGapHistoryProps {
  gaps: Array<{
    id: string;
    title: string;
    type: string;
    status: 'open' | 'filled' | 'overdue';
    createdAt: string;
    filledAt?: string;
    evidence?: string;
  }>;
  onGapClick?: (id: string) => void;
  onEvidenceFill?: (id: string, evidence: string) => void;
}

export function EvidenceGapHistory({
  gaps,
  onGapClick,
  onEvidenceFill,
}: EvidenceGapHistoryProps) {
  const [filter, setFilter] = useState<'all' | 'open' | 'filled' | 'overdue'>('all');

  const filteredGaps = gaps.filter(gap => {
    if (filter === 'all') return true;
    return gap.status === filter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'border-l-yellow-400 bg-yellow-50';
      case 'filled': return 'border-l-green-400 bg-green-50';
      case 'overdue': return 'border-l-red-400 bg-red-50';
      default: return '';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open': return <Badge variant="warning">待补充</Badge>;
      case 'filled': return <Badge variant="success">已补充</Badge>;
      case 'overdue': return <Badge variant="destructive">已逾期</Badge>;
      default: return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b pb-2">
        {(['all', 'open', 'filled', 'overdue'] as const).map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? '全部' : f === 'open' ? '待补充' : f === 'filled' ? '已补充' : '已逾期'}
            <Badge variant="secondary" className="ml-1">
              {f === 'all' ? gaps.length : gaps.filter(g => g.status === f).length}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Gap List */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-3">
          {filteredGaps.map((gap) => (
            <Card 
              key={gap.id}
              className={`border-l-4 ${getStatusColor(gap.status)}`}
              onClick={() => onGapClick?.(gap.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{gap.title}</h4>
                      {getStatusBadge(gap.status)}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{gap.type}</p>
                    {gap.evidence && (
                      <p className="text-sm mt-2 p-2 bg-white rounded border">
                        补充证据: {gap.evidence}
                      </p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span>创建: {new Date(gap.createdAt).toLocaleDateString()}</span>
                      {gap.filledAt && (
                        <span>补充: {new Date(gap.filledAt).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  {gap.status === 'open' && onEvidenceFill && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => onEvidenceFill(gap.id, '')}
                    >
                      补充证据
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

// Reminder Batch Operations Component
interface ReminderBatchOperationsProps {
  reminders: Array<{
    id: string;
    title: string;
    caseId: string;
    caseTitle: string;
    dueDate: string;
    status: 'pending' | 'completed' | 'overdue';
    priority: 'high' | 'medium' | 'low';
  }>;
  onBatchAction: (ids: string[], action: 'complete' | 'delete' | 'postpone' | 'snooze') => void;
  onReminderClick?: (id: string) => void;
}

export function ReminderBatchOperations({
  reminders,
  onBatchAction,
  onReminderClick,
}: ReminderBatchOperationsProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'overdue'>('pending');

  const filteredReminders = reminders.filter(r => {
    if (filter === 'all') return true;
    return r.status === filter;
  });

  const toggleSelect = (id: string) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedIds(newSet);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredReminders.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredReminders.map(r => r.id)));
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return '';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with Batch Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={selectedIds.size === filteredReminders.length && filteredReminders.length > 0}
            onChange={toggleSelectAll}
            className="rounded"
          />
          <span className="text-sm">
            已选择 {selectedIds.size} 项
          </span>
        </div>
        
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2">
            <Button 
              size="sm"
              onClick={() => onBatchAction(Array.from(selectedIds), 'complete')}
            >
              标记完成
            </Button>
            <Button 
              size="sm"
              variant="outline"
              onClick={() => onBatchAction(Array.from(selectedIds), 'snooze')}
            >
              稍后提醒
            </Button>
            <Button 
              size="sm"
              variant="destructive"
              onClick={() => onBatchAction(Array.from(selectedIds), 'delete')}
            >
              删除
            </Button>
          </div>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b pb-2">
        {(['all', 'pending', 'completed', 'overdue'] as const).map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? '全部' : f === 'pending' ? '待处理' : f === 'completed' ? '已完成' : '已逾期'}
            <Badge variant="secondary" className="ml-1">
              {f === 'all' ? reminders.length : reminders.filter(r => r.status === f).length}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Reminder List */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-2">
          {filteredReminders.map((reminder) => (
            <Card 
              key={reminder.id}
              className={`cursor-pointer hover:bg-muted/50 transition-colors ${
                selectedIds.has(reminder.id) ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => onReminderClick?.(reminder.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(reminder.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleSelect(reminder.id);
                    }}
                    className="rounded"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{reminder.title}</h4>
                      <span className={`text-xs ${getPriorityColor(reminder.priority)}`}>
                        {reminder.priority === 'high' ? '高优' : reminder.priority === 'medium' ? '中优' : '低优'}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {reminder.caseTitle}
                    </p>
                    <div className="flex items-center gap-4 mt-1">
                      <span className={`text-xs ${
                        reminder.status === 'overdue' ? 'text-red-600' : 
                        reminder.status === 'completed' ? 'text-green-600' : 
                        'text-muted-foreground'
                      }`}>
                        截止: {new Date(reminder.dueDate).toLocaleDateString()}
                      </span>
                      <Badge 
                        variant={
                          reminder.status === 'overdue' ? 'destructive' : 
                          reminder.status === 'completed' ? 'secondary' : 
                          'outline'
                        }
                        className="text-xs"
                      >
                        {reminder.status === 'overdue' ? '已逾期' : 
                         reminder.status === 'completed' ? '已完成' : 
                         '待处理'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
