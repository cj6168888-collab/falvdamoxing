import { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Collapsible,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import {
  ChevronUp,
  ChevronDown,
  FileText,
  Users,
  Scale,
  Clock,
  Bell,
  Settings,
  GripVertical,
  MoreHorizontal,
} from 'lucide-react';

export interface QuickAccessItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
  badge?: string | number;
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
  color?: string;
}

interface QuickAccessPanelProps {
  items: QuickAccessItem[];
  title?: string;
  defaultCollapsed?: boolean;
  maxVisibleItems?: number;
  storageKey?: string;
  onReorder?: (items: QuickAccessItem[]) => void;
  onCustomize?: () => void;
  className?: string;
}

// 快捷面板组件
export function QuickAccessPanel({
  items,
  title = '快捷操作',
  defaultCollapsed = false,
  maxVisibleItems = 6,
  onCustomize,
  className = '',
}: QuickAccessPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const visibleItems = items.slice(0, maxVisibleItems);
  const hiddenItems = items.slice(maxVisibleItems);

  const handleItemClick = useCallback((item: QuickAccessItem) => {
    if (item.onClick) {
      item.onClick();
    } else if (item.href) {
      window.location.href = item.href;
    }
  }, []);

  return (
    <Card
      className={`transition-all duration-200 ${className}`}
    >
      <CardContent className="p-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">{title}</h3>
            <Badge variant="secondary" className="text-xs">
              {items.length}
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            {onCustomize && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onCustomize}>
                <Settings className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setIsCollapsed(!isCollapsed)}
            >
              {isCollapsed ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        </div>

        {/* 折叠内容 */}
        <Collapsible open={!isCollapsed} onOpenChange={(open) => setIsCollapsed(!open)}>
          <CollapsibleContent>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
              {visibleItems.map((item) => (
                <TooltipProvider key={item.id} delayDuration={300}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleItemClick(item)}
                        className="flex flex-col items-center justify-center p-3 rounded-lg border bg-background hover:bg-muted hover:border-primary/50 transition-all group"
                      >
                        <div
                          className="h-10 w-10 rounded-full bg-muted flex items-center justify-center mb-2 group-hover:bg-primary/10 transition-colors"
                          style={item.color ? { color: item.color } : undefined}
                        >
                          {item.icon}
                        </div>
                        <span className="text-xs font-medium truncate w-full text-center">
                          {item.label}
                        </span>
                        {item.badge !== undefined && (
                          <Badge
                            variant={item.badgeVariant || 'default'}
                            className="absolute -top-1 -right-1 h-4 min-w-[1rem] px-1 text-[10px]"
                          >
                            {item.badge}
                          </Badge>
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      {item.label}
                      {item.badge !== undefined && (
                        <span className="ml-1 text-muted-foreground">({item.badge})</span>
                      )}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}

              {/* 更多按钮 */}
              {hiddenItems.length > 0 && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => setIsCollapsed(false)}
                        className="flex flex-col items-center justify-center p-3 rounded-lg border border-dashed bg-transparent hover:bg-muted/50 transition-all"
                      >
                        <MoreHorizontal className="h-10 w-10 rounded-full mb-2 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">更多</span>
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      查看全部 {items.length} 个功能
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* 已折叠时显示摘要 */}
        {isCollapsed && (
          <div className="text-xs text-muted-foreground text-center py-2">
            {visibleItems.length} 个快捷功能 · 共 {items.length} 个
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// 案件详情页底部快捷面板
interface CaseQuickAccessPanelProps {
  caseId: string;
  caseStatus?: string;
  onQuickAction?: (action: string) => void;
}

export function CaseQuickAccessPanel({
  caseId,
  caseStatus,
  onQuickAction,
}: CaseQuickAccessPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // 根据案件状态动态生成快捷操作
  const getCaseItems = (): QuickAccessItem[] => {
    const baseItems: QuickAccessItem[] = [
      {
        id: 'case-overview',
        label: '案件概览',
        icon: <FileText className="h-4 w-4" />,
        href: `/cases/${caseId}`,
      },
      {
        id: 'case-evidence',
        label: '证据管理',
        icon: <FileText className="h-4 w-4" />,
        href: `/cases/${caseId}/evidence`,
      },
      {
        id: 'case-document',
        label: '文书管理',
        icon: <FileText className="h-4 w-4" />,
        href: `/cases/${caseId}/documents`,
      },
      {
        id: 'case-party',
        label: '当事人',
        icon: <Users className="h-4 w-4" />,
        href: `/cases/${caseId}/parties`,
      },
    ];

    // 根据案件状态添加特定操作
    if (caseStatus === 'litigating' || caseStatus === 'preparing') {
      baseItems.push(
        {
          id: 'case-hearing',
          label: '出庭抗辩',
          icon: <Scale className="h-4 w-4" />,
          href: `/cases/${caseId}/hearing`,
        },
        {
          id: 'case-deadline',
          label: '期限节点',
          icon: <Clock className="h-4 w-4" />,
          href: `/cases/${caseId}/deadline`,
        }
      );
    }

    if (caseStatus === 'appealing') {
      baseItems.push({
        id: 'case-appeal',
        label: '上诉追踪',
        icon: <FileText className="h-4 w-4" />,
        href: `/cases/${caseId}/appeal`,
      });
    }

    if (caseStatus === 'executing') {
      baseItems.push({
        id: 'case-execution',
        label: '执行跟踪',
        icon: <Clock className="h-4 w-4" />,
        href: `/cases/${caseId}/execution`,
      });
    }

    baseItems.push({
      id: 'case-reminder',
      label: '提醒',
      icon: <Bell className="h-4 w-4" />,
      href: `/cases/${caseId}/reminders`,
    });

    return baseItems;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-background border-t shadow-lg">
      <div className="mx-auto max-w-6xl px-4 py-2">
        {/* 展开/收起按钮 */}
        <div className="flex items-center justify-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 px-2 text-xs gap-1"
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronUp className="h-3 w-3" />
            )}
            {isExpanded ? '收起' : '快捷功能'}
          </Button>
        </div>

        {/* 快捷功能区 */}
        {isExpanded && (
          <div className="mt-2">
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {getCaseItems().map((item) => (
                <TooltipProvider key={item.id} delayDuration={300}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-shrink-0 gap-2"
                        onClick={() => {
                          if (item.href) {
                            window.location.href = item.href;
                          } else if (item.onClick) {
                            item.onClick();
                          }
                        }}
                        onDoubleClick={() => onQuickAction?.(item.id)}
                      >
                        {item.icon}
                        <span className="text-xs">{item.label}</span>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      {item.label}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// 可拖拽排序的快捷面板
interface SortableQuickAccessProps {
  items: QuickAccessItem[];
  onItemsChange: (items: QuickAccessItem[]) => void;
  onEdit?: () => void;
}

export function SortableQuickAccess({
  items,
  onItemsChange,
  onEdit,
}: SortableQuickAccessProps) {
  const [editing, setEditing] = useState(false);

  const handleDragStart = (e: React.DragEvent, index: number) => {
    e.dataTransfer.setData('text/plain', index.toString());
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    const sourceIndex = parseInt(e.dataTransfer.getData('text/plain'));

    if (sourceIndex === targetIndex) return;

    const newItems = [...items];
    const [removed] = newItems.splice(sourceIndex, 1);
    newItems.splice(targetIndex, 0, removed);

    onItemsChange(newItems);
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">自定义快捷功能</h3>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => setEditing(!editing)}>
              {editing ? '完成' : '编辑'}
            </Button>
            {onEdit && (
              <Button variant="outline" size="sm" onClick={onEdit}>
                添加
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {items.map((item, index) => (
            <div
              key={item.id}
              draggable={editing}
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, index)}
              className={`flex items-center gap-2 p-3 rounded-lg border bg-background ${
                editing ? 'cursor-move hover:bg-muted' : ''
              }`}
            >
              {editing && (
                <GripVertical className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              )}
              <div
                className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0"
                style={item.color ? { color: item.color } : undefined}
              >
                {item.icon}
              </div>
              <span className="text-sm truncate flex-1">{item.label}</span>
              {editing && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 flex-shrink-0"
                  onClick={() => onItemsChange(items.filter((i) => i.id !== item.id))}
                >
                  ×
                </Button>
              )}
            </div>
          ))}
        </div>

        {editing && (
          <p className="text-xs text-muted-foreground mt-3 text-center">
            拖拽以排序，点击 × 删除
          </p>
        )}
      </CardContent>
    </Card>
  );
}
