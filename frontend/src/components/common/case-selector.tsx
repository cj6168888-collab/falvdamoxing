import { Plus, Search, Filter, CheckSquare } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface CaseListHeaderProps {
  search: string;
  onSearchChange: (value: string) => void;
  onNewCase: () => void;
  searchPlaceholder?: string;
  newCaseLabel?: string;
  /** 进入批量操作模式 */
  onBatchMode?: () => void;
}

export function CaseListHeader({
  search,
  onSearchChange,
  onNewCase,
  searchPlaceholder = '搜索案件名称/当事人/案号...',
  newCaseLabel = '新建案件',
  onBatchMode,
}: CaseListHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-1 items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" size="icon">
          <Filter className="h-4 w-4" />
        </Button>
        {onBatchMode && (
          <Button
            variant="outline"
            size="sm"
            onClick={onBatchMode}
            className="gap-1"
            aria-label="批量操作"
            title="批量操作"
          >
            <CheckSquare className="h-4 w-4" />
            <span className="hidden sm:inline">批量操作</span>
          </Button>
        )}
      </div>
      <Button onClick={onNewCase}>
        <Plus className="mr-2 h-4 w-4" />
        {newCaseLabel}
      </Button>
    </div>
  );
}
