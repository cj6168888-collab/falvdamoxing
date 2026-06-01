import { useNavigate } from 'react-router-dom';
import { CaseListHeader } from '@/components/common/case-selector';
import { CaseCard } from '@/components/common/case-card';
import { useCaseList } from '@/hooks/use-case';
import { useCaseActions } from '@/hooks/use-case-actions';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Trash2,
  Archive,
  Download,
  X,
  Check,
  Loader2,
} from 'lucide-react';
import { useAuthStore } from '@/stores/auth.store';
import { getAudienceLabels } from '@/lib/audience-copy';

export default function CasesListPage() {
  const navigate = useNavigate();
  const tenantType = useAuthStore((s) => s.tenant?.tenant_type);
  const labels = getAudienceLabels(tenantType);
  const [search, setSearch] = useState('');
  const [batchMode, setBatchMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const { data, isLoading, isError } = useCaseList({ search: search || undefined });
  const caseActions = useCaseActions();

  const filteredCases = useMemo(() => data && search
    ? data.filter(c =>
        c.title?.includes(search) ||
        c.plaintiff?.name?.includes(search) ||
        c.defendant?.name?.includes(search)
      )
    : data || [], [data, search]);

  const selectedCount = selectedIds.size;

  const allSelected = useMemo(() => {
    return filteredCases.length > 0 && selectedIds.size === filteredCases.length;
  }, [filteredCases.length, selectedIds.size]);

  const handleSelect = useCallback((caseId: string, selected: boolean) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (selected) {
        next.add(caseId);
      } else {
        next.delete(caseId);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredCases.map(c => c.id)));
    }
  }, [allSelected, filteredCases]);

  const handleExitBatchMode = useCallback(() => {
    setBatchMode(false);
    setSelectedIds(new Set());
  }, []);

  const handleBatchDelete = async () => {
    setActionLoading(true);
    try {
      const deletePromises = Array.from(selectedIds).map(id =>
        caseActions.deleteCase.mutateAsync(id)
      );
      await Promise.all(deletePromises);
      setDeleteDialogOpen(false);
      handleExitBatchMode();
    } catch (error) {
      console.error('批量删除失败:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBatchArchive = async () => {
    setActionLoading(true);
    try {
      const archivePromises = Array.from(selectedIds).map(id =>
        caseActions.updateCase.mutateAsync({ id, data: { status: 'closed' } })
      );
      await Promise.all(archivePromises);
      setArchiveDialogOpen(false);
      handleExitBatchMode();
    } catch (error) {
      console.error('批量归档失败:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBatchExport = async () => {
    const selectedCases = filteredCases.filter(c => selectedIds.has(c.id));
    const exportData = selectedCases.map(c => ({
      id: c.id,
      title: c.title,
      type: c.type,
      plaintiff: c.plaintiff?.name,
      defendant: c.defendant?.name,
      status: c.status,
      amount: c.amount,
      created_at: c.createdAt,
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cases-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    handleExitBatchMode();
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <CaseListHeader
        search={search}
        onSearchChange={setSearch}
        onNewCase={() => navigate('/cases/new')}
        searchPlaceholder={labels.searchPlaceholder}
        newCaseLabel={labels.newCase}
        onBatchMode={() => setBatchMode(true)}
      />

      {/* 批量操作栏 */}
      {batchMode && (
        <div className="mt-4 flex items-center justify-between rounded-lg border bg-muted/50 px-4 py-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Checkbox
                checked={allSelected}
                ref={(el) => {
                  if (el) {
                    (el as unknown as { indeterminate: boolean }).indeterminate = selectedCount > 0 && !allSelected;
                  }
                }}
                onCheckedChange={handleSelectAll}
                aria-label="全选"
              />
              <Label className="cursor-pointer" onClick={handleSelectAll}>
                全选 ({selectedCount}/{filteredCases.length})
              </Label>
            </div>
            {selectedCount > 0 && (
              <span className="text-sm text-muted-foreground">
                已选择 {selectedCount} {labels.selectedUnit}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {selectedCount > 0 ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBatchExport}
                  className="gap-1"
                >
                  <Download className="h-4 w-4" />
                  导出
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setArchiveDialogOpen(true)}
                  className="gap-1"
                >
                  <Archive className="h-4 w-4" />
                  归档
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setDeleteDialogOpen(true)}
                  className="gap-1"
                >
                  <Trash2 className="h-4 w-4" />
                  删除
                </Button>
              </>
            ) : (
              <span className="text-sm text-muted-foreground">请选择要操作的{labels.caseNoun}</span>
            )}

            <div className="ml-2 border-l pl-2">
              <Button variant="ghost" size="sm" onClick={handleExitBatchMode} className="gap-1">
                <X className="h-4 w-4" />
                退出
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6">
        {isLoading && <PageSkeleton />}
        {isError && (
          <EmptyState
            title="加载失败"
            description="请检查网络连接"
            actionLabel="重试"
            onAction={() => window.location.reload()}
          />
        )}
        {!isLoading && !isError && filteredCases.length === 0 && (
          <EmptyState
            title={labels.emptyTitle}
            description={labels.emptyDescription}
            actionLabel={labels.newCase}
            onAction={() => navigate('/cases/new')}
          />
        )}
        {!isLoading && !isError && filteredCases.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredCases.map((c) => (
              <CaseCard
                key={c.id}
                caseData={c}
                selectable={batchMode}
                selected={selectedIds.has(c.id)}
                onSelect={handleSelect}
                labels={{
                  plaintiffLabel: labels.plaintiffLabel,
                  defendantLabel: labels.defendantLabel,
                  evidenceLabel: labels.evidenceTab,
                  documentLabel: labels.documentsTab,
                  deadlineLabel: labels.timelineTab,
                  selectPrefix: `选择${labels.caseNoun}`,
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认批量删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除选中的 {selectedCount} {labels.selectedUnit}吗？此操作不可撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchDelete}
              disabled={actionLoading}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {actionLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  删除中...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  确认删除
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 归档确认对话框 */}
      <AlertDialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认批量归档</AlertDialogTitle>
            <AlertDialogDescription>
              {labels.batchArchiveDescription.replace('{count}', String(selectedCount))}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleBatchArchive} disabled={actionLoading}>
              {actionLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  归档中...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  确认归档
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
