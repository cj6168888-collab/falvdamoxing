import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  FolderOpen,
  FolderSync,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  File,
  Play,
  Square,
  Loader2,
  type LucideIcon,
} from 'lucide-react';
import { useFolderStatus, useEnableMonitoring, useDisableMonitoring, useTriggerScan, useUpdateFolderConfig } from '@/api/evidence-folder.api';
import { toast } from 'sonner';

interface EvidenceFolderCardProps {
  caseId: string;
}

function getApiErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { detail?: string } } }).response;
  const message = (error as { message?: string }).message;
  return response?.data?.detail || message || fallback;
}

export default function EvidenceFolderCard({ caseId }: EvidenceFolderCardProps) {
  const caseIdNum = parseInt(caseId, 10);
  const [folderPath, setFolderPath] = useState('');
  const [savingPath, setSavingPath] = useState(false);

  const { data: status, isLoading, isError, error, refetch } = useFolderStatus(caseIdNum);
  const enableMonitor = useEnableMonitoring(caseIdNum);
  const disableMonitor = useDisableMonitoring(caseIdNum);
  const triggerScan = useTriggerScan(caseIdNum);
  const updateConfig = useUpdateFolderConfig(caseIdNum);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">加载中...</span>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">API 连接失败</span>
          </div>
          <p className="mt-2 text-sm text-red-500">
            {(error as Error)?.message || '无法连接到证据文件夹 API'}
          </p>
          <Button size="sm" className="mt-3" onClick={() => refetch()}>
            <RefreshCw className="mr-1 h-4 w-4" />重试
          </Button>
        </CardContent>
      </Card>
    );
  }

  const handleSavePath = async () => {
    if (!folderPath.trim()) {
      toast.error('请输入文件夹路径');
      return;
    }
    setSavingPath(true);
    try {
      console.log('[EvidenceFolder] Saving path:', folderPath.trim());
      await updateConfig.mutateAsync({ folder_path: folderPath.trim(), enabled: true });
      toast.success('文件夹路径已保存，监控已启用');
      setFolderPath('');
      refetch();
    } catch (err: unknown) {
      const errorMsg = getApiErrorMessage(err, '保存路径失败');
      console.error('[EvidenceFolder] Save path error:', err);
      toast.error(errorMsg);
    } finally {
      setSavingPath(false);
    }
  };

  const handleEnableMonitoring = async () => {
    if (!status?.folder_path) {
      toast.error('请先配置文件夹路径');
      return;
    }
    try {
      console.log('[EvidenceFolder] Enabling monitoring for case:', caseIdNum);
      await enableMonitor.mutateAsync();
      toast.success('文件夹监控已启用');
      refetch();
    } catch (err: unknown) {
      const errorMsg = getApiErrorMessage(err, '启用监控失败');
      console.error('[EvidenceFolder] Enable monitoring error:', err);
      toast.error(errorMsg);
    }
  };

  const handleDisableMonitoring = async () => {
    try {
      console.log('[EvidenceFolder] Disabling monitoring for case:', caseIdNum);
      await disableMonitor.mutateAsync();
      toast.success('文件夹监控已停用');
      refetch();
    } catch (err: unknown) {
      const errorMsg = getApiErrorMessage(err, '停用监控失败');
      console.error('[EvidenceFolder] Disable monitoring error:', err);
      toast.error(errorMsg);
    }
  };

  const handleScan = async (type: 'full' | 'incremental') => {
    if (!status?.folder_path) {
      toast.error('请先配置文件夹路径');
      return;
    }
    if (!status?.folder_exists) {
      toast.error('文件夹路径不存在，请检查路径是否正确');
      return;
    }
    try {
      console.log('[EvidenceFolder] Starting', type, 'scan for case:', caseIdNum);
      await triggerScan.mutateAsync(type);
      toast.success(type === 'full' ? '全量扫描已在后台启动' : '增量扫描已在后台启动');
      refetch();
    } catch (err: unknown) {
      const errorMsg = getApiErrorMessage(err, '扫描失败');
      console.error('[EvidenceFolder] Scan error:', err);
      toast.error(errorMsg);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <FolderSync className="h-5 w-5" />
            证据文件夹
          </CardTitle>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleScan('full')}
              disabled={triggerScan.isPending || !status?.folder_path || !status?.folder_exists}
            >
              <RefreshCw className={`mr-1 h-4 w-4 ${triggerScan.isPending ? 'animate-spin' : ''}`} />
              全量扫描
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleScan('incremental')}
              disabled={triggerScan.isPending || !status?.folder_path || !status?.folder_exists}
            >
              <RefreshCw className={`mr-1 h-4 w-4 ${triggerScan.isPending ? 'animate-spin' : ''}`} />
              增量扫描
            </Button>
            {status?.is_monitoring ? (
              <Button
                size="sm"
                variant="destructive"
                onClick={handleDisableMonitoring}
                disabled={disableMonitor.isPending}
              >
                <Square className="mr-1 h-4 w-4" />
                停止监控
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={handleEnableMonitoring}
                disabled={enableMonitor.isPending}
              >
                <Play className="mr-1 h-4 w-4" />
                启动监控
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 路径配置 */}
        {!status?.folder_path ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FolderOpen className="h-4 w-4" />
              <span>配置证据文件夹路径</span>
            </div>
            <div className="flex gap-2">
              <Input
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder="输入文件夹路径，如 D:\案件资料\证据"
                className="flex-1"
                onKeyDown={(e) => { if (e.key === 'Enter') handleSavePath(); }}
              />
              <Button
                size="sm"
                disabled={!folderPath.trim() || savingPath}
                onClick={handleSavePath}
              >
                {savingPath ? '保存中...' : '保存'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              提示：路径保存后可点击"启动监控"实时监听新文件
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm">
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
            <code className="rounded bg-muted px-2 py-1 text-xs">{status.folder_path}</code>
          </div>
        )}

        {/* 状态指示 */}
        <div className="flex items-center gap-4">
          <Badge variant={status?.is_monitoring ? 'default' : 'secondary'}>
            {status?.is_monitoring ? '监控中' : '未监控'}
          </Badge>
          {status?.last_scan_time && (
            <span className="text-sm text-muted-foreground">
              最后扫描: {new Date(status.last_scan_time).toLocaleString('zh-CN')}
            </span>
          )}
        </div>

        {/* 统计 */}
        {status?.stats && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            <StatCard label="总文件" value={status.stats.total} icon={File} />
            <StatCard label="已处理" value={status.stats.processed} icon={CheckCircle} color="text-green-600" />
            <StatCard label="待处理" value={status.stats.pending} icon={Clock} color="text-yellow-600" />
            <StatCard label="处理失败" value={status.stats.failed} icon={AlertCircle} color="text-red-600" />
            <StatCard label="已跳过" value={status.stats.skipped} icon={File} color="text-gray-400" />
          </div>
        )}

        {/* 最近处理的文件 */}
        {status?.recent_files && status.recent_files.length > 0 && (
          <div>
            <h4 className="mb-2 text-sm font-medium">最近处理</h4>
            <div className="space-y-1">
              {status.recent_files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between rounded border px-3 py-2 text-sm"
                >
                  <div className="flex items-center gap-2 truncate">
                    <File className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                    <span className="truncate">{file.file_name}</span>
                  </div>
                  <FileStatusBadge status={file.status} />
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'text-muted-foreground',
}: {
  label: string;
  value: number;
  icon: LucideIcon;
  color?: string;
}) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className={`mt-1 text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function FileStatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' }> = {
    completed: { label: '已完成', variant: 'default' },
    processing: { label: '处理中', variant: 'secondary' },
    pending: { label: '待处理', variant: 'secondary' },
    failed: { label: '失败', variant: 'destructive' },
    skipped: { label: '已跳过', variant: 'secondary' },
  };

  const c = config[status] || { label: status, variant: 'secondary' };

  return <Badge variant={c.variant} className="text-xs">{c.label}</Badge>;
}
