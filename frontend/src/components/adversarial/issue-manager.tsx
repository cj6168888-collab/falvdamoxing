import { Button } from '@/components/ui/button';
import { IssueCard } from './issue-card';
import { Plus } from 'lucide-react';
import type { Issue } from '@/types/issue.types';

interface Props { caseId: string; issues: Issue[]; isLoading: boolean; onAdd: () => void; onSelect: (issue: Issue) => void; }

export function IssueManager({ caseId: _caseId, issues, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-20 rounded bg-muted" /><div className="h-20 rounded bg-muted" /></div>;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">争点管理</h3>
        <Button size="sm" onClick={onAdd}><Plus className="mr-2 h-4 w-4" />新增争点</Button>
      </div>
      {!issues?.length ? <p className="text-muted-foreground text-center py-8">暂无争点</p> : (
        <div className="grid gap-4 sm:grid-cols-2">{issues.map((i) => (<IssueCard key={i.id} issue={i} onClick={() => onSelect(i)} />))}</div>
      )}
    </div>
  );
}
