import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreVertical, ChevronUp, ChevronDown } from 'lucide-react';

export interface ActionButton {
  id: string;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  disabled?: boolean;
  className?: string;
}

interface ActionBarProps {
  /** 主要操作按钮（桌面端平铺） */
  primaryActions?: ActionButton[];
  /** 次要/更多操作（手机端折叠到 ... 菜单） */
  secondaryActions?: ActionButton[];
  /** 是否显示展开/折叠按钮 */
  collapsible?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

export function ActionBar({
  primaryActions = [],
  secondaryActions = [],
  collapsible = false,
  defaultExpanded = false,
  className = '',
}: ActionBarProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const allSecondaryActions = [...primaryActions.slice(3), ...secondaryActions];
  const visiblePrimaryActions = primaryActions.slice(0, 3);

  if (primaryActions.length === 0 && secondaryActions.length === 0) {
    return null;
  }

  return (
    <div className={`flex items-center justify-between ${className}`}>
      {/* 左侧：展开/折叠按钮 */}
      {collapsible && (
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-muted-foreground"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? '折叠操作栏' : '展开操作栏'}
        >
          {isExpanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </Button>
      )}

      {/* 主要操作按钮 - 桌面端平铺 */}
      <div className="hidden sm:flex items-center gap-0.5">
        {visiblePrimaryActions.map((action) => (
          <Button
            key={action.id}
            variant={action.variant || 'ghost'}
            size="sm"
            className="h-6 w-6 p-0"
            onClick={action.onClick}
            disabled={action.disabled}
            title={action.label}
          >
            {action.icon}
          </Button>
        ))}
        {/* 更多操作菜单 - 桌面端 */}
        {allSecondaryActions.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                <MoreVertical className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {primaryActions.slice(3).map((action) => (
                <DropdownMenuItem
                  key={action.id}
                  onClick={action.onClick}
                  disabled={action.disabled}
                >
                  <span className="mr-2">{action.icon}</span>
                  {action.label}
                </DropdownMenuItem>
              ))}
              {primaryActions.slice(3).length > 0 && secondaryActions.length > 0 && (
                <DropdownMenuSeparator />
              )}
              {secondaryActions.map((action) => (
                <DropdownMenuItem
                  key={action.id}
                  onClick={action.onClick}
                  disabled={action.disabled}
                >
                  <span className="mr-2">{action.icon}</span>
                  {action.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* 手机端：所有按钮折叠到 ... 菜单 */}
      <div className="sm:hidden">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              <MoreVertical className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            {primaryActions.map((action) => (
              <DropdownMenuItem
                key={action.id}
                onClick={action.onClick}
                disabled={action.disabled}
              >
                <span className="mr-2">{action.icon}</span>
                {action.label}
              </DropdownMenuItem>
            ))}
            {secondaryActions.length > 0 && primaryActions.length > 0 && (
              <DropdownMenuSeparator />
            )}
            {secondaryActions.map((action) => (
              <DropdownMenuItem
                key={action.id}
                onClick={action.onClick}
                disabled={action.disabled}
              >
                <span className="mr-2">{action.icon}</span>
                {action.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

export default ActionBar;
