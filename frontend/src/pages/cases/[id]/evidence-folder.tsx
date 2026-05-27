import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  FolderOpen, FolderSync, RefreshCw, CheckCircle, Clock,
  AlertCircle, File, Play, Square, Loader2, Eye, Trash2, RotateCw
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { toast } from 'sonner';

interface FolderStatus {
  case_id: number;
  folder_path: string | null;
  folder_exists: boolean;
  enabled: boolean;
  is_monitoring: boolean;
  last_scan_time: string | null;
  stats: {
    total: number;
    processed: number;
    processing?: number;
    pending: number;
    failed: number;
    skipped: number;
  };
  recent_files: {
    id: number;
    file_name: string;
    status: string;
    error_message: string | null;
    auto_category: string | null;
    evidence_id: string | null;
    processed_at: string | null;
  }[];
}

interface FolderFileRecord {
  id: number;
  file_name: string;
  file_extension: string;
  file_size: number | null;
  auto_category: string | null;
  auto_summary: string | null;
  status: string;
  error_message: string | null;
  evidence_id: string | null;
  processed_at: string | null;
  detected_at: string;
}

interface DirectoryPickerHandle {
  name: string;
}

interface DirectoryPickerWindow {
  showDirectoryPicker?: (options: { mode: 'read' }) => Promise<DirectoryPickerHandle>;
}

interface WebkitDirectoryInput extends HTMLInputElement {
  webkitdirectory: boolean;
}

export default function CaseEvidenceFolderPage() {
  const { id } = useParams<{ id: string }>();
  const caseIdNum = parseInt(id || '0', 10);
  const queryClient = useQueryClient();

  const [folderPath, setFolderPath] = useState('');
  const [savingPath, setSavingPath] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FolderFileRecord | null>(null);
  const [showFileDetail, setShowFileDetail] = useState(false);

  // 获取文件夹状态（每 2 秒轮询，显示实时识别状态）
  const { data: status, isLoading: loadingStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['evidence-folder-status', caseIdNum],
    queryFn: () => axiosInstance.get<FolderStatus>(`/api/evidence-folder/cases/${caseIdNum}/status`).then(res => res.data),
    enabled: !!caseIdNum,
    refetchInterval: (query) => {
      const folderStatus = query.state.data;
      if (!folderStatus) return 5000;
      const isBusy = folderStatus.is_monitoring || (folderStatus.stats && folderStatus.stats.pending > 0);
      return isBusy ? 2000 : 5000;
    },
  });

  // 获取文件列表（每 2 秒轮询，显示实时识别状态）
  const { data: filesData, refetch: refetchFiles } = useQuery({
    queryKey: ['evidence-folder-files', caseIdNum],
    queryFn: () => axiosInstance.get<{ records: FolderFileRecord[] }>(`/api/evidence-folder/cases/${caseIdNum}/files`).then(res => res.data),
    enabled: !!caseIdNum,
    refetchInterval: (query) => {
      const fileList = query.state.data;
      if (!fileList || !fileList.records) return 5000;
      const hasPending = fileList.records.some((r) => r.status === 'pending' || r.status === 'processing');
      return hasPending ? 2000 : 5000;
    },
  });

  // 保存路径
  const savePathMutation = useMutation({
    mutationFn: (path: string) =>
      axiosInstance.put(`/api/evidence-folder/cases/${caseIdNum}/config`, {
        folder_path: path,
        enabled: true,
      }),
    onSuccess: () => {
      toast.success('文件夹已配置，正在后台扫描文件...');
      setFolderPath('');
      // 立即刷新状态和文件列表
      setTimeout(() => {
        refetchStatus();
        refetchFiles();
      }, 1000);
    },
    onError: (err) => {
      toast.error(getRequestErrorMessage(err, '保存路径失败'));
    },
  });

  // 全量扫描
  const fullScanMutation = useMutation({
    mutationFn: () =>
      axiosInstance.post(`/api/evidence-folder/cases/${caseIdNum}/scan`, { scan_type: 'full' }),
    onSuccess: () => {
      toast.success('全量扫描已在后台启动，请稍后查看结果');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
        queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseIdNum] });
      }, 3000);
    },
    onError: (err) => {
      toast.error(getRequestErrorMessage(err, '扫描失败'));
    },
  });

  // 增量扫描
  const incrementalScanMutation = useMutation({
    mutationFn: () =>
      axiosInstance.post(`/api/evidence-folder/cases/${caseIdNum}/scan-incremental`),
    onSuccess: () => {
      toast.success('增量扫描已在后台启动');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
        queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseIdNum] });
      }, 3000);
    },
    onError: (err) => {
      toast.error(getRequestErrorMessage(err, '扫描失败'));
    },
  });

  // 启动监控
  const enableMonitorMutation = useMutation({
    mutationFn: () =>
      axiosInstance.post(`/api/evidence-folder/cases/${caseIdNum}/enable-monitor`),
    onSuccess: () => {
      toast.success('文件夹监控已启用，新文件将自动处理');
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
    },
    onError: (err) => {
      toast.error(getRequestErrorMessage(err, '启用监控失败'));
    },
  });

  // 停止监控
  const disableMonitorMutation = useMutation({
    mutationFn: () =>
      axiosInstance.post(`/api/evidence-folder/cases/${caseIdNum}/disable-monitor`),
    onSuccess: () => {
      toast.success('文件夹监控已停用');
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
    },
    onError: (err) => {
      toast.error(getRequestErrorMessage(err, '停用监控失败'));
    },
  });

  // 重新处理文件
  const reprocessMutation = useMutation({
    mutationFn: (fileId: number) =>
      axiosInstance.post(`/api/evidence-folder/cases/${caseIdNum}/files/${fileId}/reprocess`),
    onSuccess: () => {
      toast.success('已重新提交处理');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseIdNum] });
        queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
      }, 2000);
    },
    onError: () => toast.error('重新处理失败'),
  });

  // 批量重新处理所有失败文件
  const reprocessAllFailedMutation = useMutation({
    mutationFn: async () => {
      const failedFiles = files.filter(f => f.status === 'failed');
      if (failedFiles.length === 0) {
        toast.info('没有失败的文件需要重新处理');
        return 0;
      }
      toast.info(`正在重新处理 ${failedFiles.length} 个失败文件...`);
      for (const file of failedFiles) {
        try {
          await axiosInstance.post(`/api/evidence-folder/cases/${caseIdNum}/files/${file.id}/reprocess`);
        } catch (err) {
          console.error(`重新处理文件 ${file.file_name} 失败:`, err);
        }
      }
      return failedFiles.length;
    },
    onSuccess: (count) => {
      if (count > 0) {
        toast.success(`已重新提交 ${count} 个文件处理`);
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseIdNum] });
          queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
        }, 3000);
      }
    },
    onError: () => toast.error('批量重新处理失败'),
  });

  // 删除文件记录
  const deleteFileMutation = useMutation({
    mutationFn: (fileId: number) =>
      axiosInstance.delete(`/api/evidence-folder/cases/${caseIdNum}/files/${fileId}`),
    onSuccess: () => {
      toast.success('文件记录已删除');
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-files', caseIdNum] });
      queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
    },
    onError: () => toast.error('删除失败'),
  });

  const handleSelectFolder = async () => {
    // 尝试使用现代浏览器的文件夹选择 API
    const directoryWindow = window as unknown as DirectoryPickerWindow;
    if (directoryWindow.showDirectoryPicker) {
      try {
        const dirHandle = await directoryWindow.showDirectoryPicker({
          mode: 'read',
        });
        // 获取文件夹路径（浏览器安全限制，只能获取相对名称）
        const folderName = dirHandle.name;
        setFolderPath(folderName);
        // 尝试保存
        await handleSavePathWithHandle(folderName, dirHandle);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === 'AbortError')) {
          toast.error('选择文件夹失败：' + getRequestErrorMessage(err, '未知错误'));
        }
      }
    } else {
      // 降级方案：使用文件输入框让用户选择文件夹
      const input = document.createElement('input');
      input.type = 'file';
      (input as WebkitDirectoryInput).webkitdirectory = true;
      input.onchange = async (e: Event) => {
        const files = (e.target as HTMLInputElement | null)?.files;
        if (files && files.length > 0) {
          // 从文件路径中提取文件夹名称
          const pathParts = files[0].webkitRelativePath.split('/');
          if (pathParts.length > 1) {
            const folderName = pathParts[0];
            setFolderPath(folderName);
            try {
              await savePathMutation.mutateAsync(folderName);
              toast.success(`文件夹"${folderName}"已配置，监控已启用`);
              setFolderPath('');
              queryClient.invalidateQueries({ queryKey: ['evidence-folder-status', caseIdNum] });
            } catch (err) {
              toast.error(getRequestErrorMessage(err, '保存路径失败'));
            }
          }
        }
      };
      input.click();
    }
  };

  const handleSavePathWithHandle = async (folderName: string, _dirHandle: DirectoryPickerHandle) => {
    setSavingPath(true);
    try {
      await savePathMutation.mutateAsync(folderName);
    } catch (err) {
      toast.error(getRequestErrorMessage(err, '保存路径失败'));
    } finally {
      setSavingPath(false);
    }
  };

  const handleSavePath = async () => {
    if (!folderPath.trim()) {
      toast.error('请输入文件夹路径');
      return;
    }
    setSavingPath(true);
    try {
      await savePathMutation.mutateAsync(folderPath.trim());
    } catch (err) {
      toast.error(getRequestErrorMessage(err, '保存路径失败'));
    } finally {
      setSavingPath(false);
    }
  };

  const files: FolderFileRecord[] = filesData?.records || [];

  if (loadingStatus) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">加载证据文件夹状态...</span>
        </CardContent>
      </Card>
    );
  }

  // 文件详情视图
  if (showFileDetail && selectedFile) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => { setShowFileDetail(false); setSelectedFile(null); }}>
            ← 返回列表
          </Button>
          <h2 className="text-xl font-bold">{selectedFile.file_name}</h2>
          <Badge>{selectedFile.auto_category || '未分类'}</Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle>文件信息</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-muted-foreground">文件名：</span>{selectedFile.file_name}</div>
                <div><span className="text-muted-foreground">类型：</span>{selectedFile.file_extension}</div>
                <div><span className="text-muted-foreground">大小：</span>{selectedFile.file_size ? formatFileSize(selectedFile.file_size) : '-'}</div>
                <div><span className="text-muted-foreground">状态：</span><StatusBadge status={selectedFile.status} /></div>
                <div><span className="text-muted-foreground">自动分类：</span>{selectedFile.auto_category || '未分类'}</div>
                <div><span className="text-muted-foreground">检测时间：</span>{selectedFile.detected_at ? new Date(selectedFile.detected_at).toLocaleString('zh-CN') : '-'}</div>
                <div><span className="text-muted-foreground">处理时间：</span>{selectedFile.processed_at ? new Date(selectedFile.processed_at).toLocaleString('zh-CN') : '-'}</div>
                <div><span className="text-muted-foreground">关联证据：</span>{selectedFile.evidence_id || '未关联'}</div>
              </div>
              {selectedFile.error_message && (
                <div className="text-red-500 text-xs">
                  <AlertCircle className="h-3 w-3 inline mr-1" />
                  错误：{selectedFile.error_message}
                </div>
              )}
              {selectedFile.auto_summary && (
                <div>
                  <span className="text-muted-foreground">自动摘要：</span>
                  <p className="text-xs mt-1 text-muted-foreground">{selectedFile.auto_summary}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(selectedFile.status === 'failed' || selectedFile.status === 'completed') && (
                <Button
                  className="w-full"
                  onClick={() => reprocessMutation.mutate(selectedFile.id)}
                  disabled={reprocessMutation.isPending}
                >
                  <RotateCw className="mr-1 h-4 w-4" />
                  重新处理
                </Button>
              )}
              <Button
                variant="destructive"
                className="w-full"
                onClick={() => deleteFileMutation.mutate(selectedFile.id)}
                disabled={deleteFileMutation.isPending}
              >
                <Trash2 className="mr-1 h-4 w-4" />
                删除记录
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 文件夹配置 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderSync className="h-5 w-5" />
            证据文件夹配置
          </CardTitle>
          <CardDescription>
            指定本地文件夹路径，系统将自动扫描、分类、处理其中的证据文件
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 路径配置 */}
          {!status?.folder_path ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FolderOpen className="h-4 w-4" />
                <span>选择证据文件夹</span>
              </div>
              <div className="flex flex-col gap-2">
                <Button
                  size="lg"
                  onClick={handleSelectFolder}
                  disabled={savingPath}
                  className="w-full"
                >
                  <FolderOpen className="mr-2 h-5 w-5" />
                  {savingPath ? '配置中...' : '选择文件夹'}
                </Button>
                <div className="flex items-center gap-2">
                  <div className="h-px flex-1 bg-border" />
                  <span className="text-xs text-muted-foreground">或手动输入路径</span>
                  <div className="h-px flex-1 bg-border" />
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
              </div>
              <p className="text-xs text-muted-foreground">
                提示：选择文件夹后，系统将自动扫描其中的所有证据文件
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <FolderOpen className="h-4 w-4 text-muted-foreground" />
                <code className="rounded bg-muted px-2 py-1 text-xs">{status.folder_path}</code>
                <Badge variant={status.folder_exists ? 'default' : 'destructive'} className="text-xs">
                  {status.folder_exists ? '路径存在' : '路径不存在'}
                </Badge>
              </div>

              {/* 操作按钮 */}
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => fullScanMutation.mutate()}
                  disabled={fullScanMutation.isPending || !status?.folder_exists}
                >
                  <RefreshCw className={`mr-1 h-4 w-4 ${fullScanMutation.isPending ? 'animate-spin' : ''}`} />
                  全量扫描
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => incrementalScanMutation.mutate()}
                  disabled={incrementalScanMutation.isPending || !status?.folder_exists}
                >
                  <RefreshCw className={`mr-1 h-4 w-4 ${incrementalScanMutation.isPending ? 'animate-spin' : ''}`} />
                  增量扫描
                </Button>
                {status?.stats && status.stats.failed > 0 && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-amber-600 border-amber-300"
                    onClick={() => reprocessAllFailedMutation.mutate()}
                    disabled={reprocessAllFailedMutation.isPending}
                  >
                    <RotateCw className={`mr-1 h-4 w-4 ${reprocessAllFailedMutation.isPending ? 'animate-spin' : ''}`} />
                    重新处理失败文件 ({status.stats.failed})
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => { refetchStatus(); refetchFiles(); }}
                >
                  <Eye className="mr-1 h-4 w-4" />
                  刷新状态
                </Button>
                {status?.is_monitoring ? (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => disableMonitorMutation.mutate()}
                    disabled={disableMonitorMutation.isPending}
                  >
                    <Square className="mr-1 h-4 w-4" />
                    停止监控
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => enableMonitorMutation.mutate()}
                    disabled={enableMonitorMutation.isPending || !status?.folder_exists}
                  >
                    <Play className="mr-1 h-4 w-4" />
                    启动监控
                  </Button>
                )}
              </div>

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
            </div>
          )}
        </CardContent>
      </Card>

      {/* 统计概览 */}
      {status?.stats && status.folder_path && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <StatCard label="总文件" value={status.stats.total} icon={File} />
          <StatCard label="已处理" value={status.stats.processed} icon={CheckCircle} color="text-green-600" />
          <StatCard label="待处理" value={status.stats.pending} icon={Clock} color="text-yellow-600" />
          <StatCard label="处理失败" value={status.stats.failed} icon={AlertCircle} color="text-red-600" />
          <StatCard label="已跳过" value={status.stats.skipped} icon={File} color="text-gray-400" />
        </div>
      )}

      {/* 最近处理的文件 */}
      {status?.recent_files && status.recent_files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>最近处理的文件</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {status.recent_files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between rounded border px-3 py-2 text-sm hover:bg-muted/50 cursor-pointer"
                  onClick={() => { setSelectedFile(folderRecentFileToRecord(file)); setShowFileDetail(true); }}
                >
                  <div className="flex items-center gap-2 truncate">
                    <File className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                    <span className="truncate">{file.file_name}</span>
                    {file.auto_category && (
                      <Badge variant="outline" className="text-xs">{file.auto_category}</Badge>
                    )}
                  </div>
                  <StatusBadge status={file.status} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 文件列表 - 始终显示，有路径就显示 */}
      {status?.folder_path && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span>文件列表 ({files.length})</span>
                {status?.stats && status.stats.pending > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    正在识别 {status.stats.pending} 个文件...
                  </Badge>
                )}
                {status?.stats && (status.stats.processing ?? 0) > 0 && (
                  <Badge variant="outline" className="text-xs">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    处理中 {status.stats.processing ?? 0} 个
                  </Badge>
                )}
              </div>
              <Button size="sm" variant="outline" onClick={() => { refetchStatus(); refetchFiles(); }}>
                <RefreshCw className="mr-1 h-4 w-4" />刷新
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {files.length === 0 ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                <FolderOpen className="mx-auto h-8 w-8 opacity-50 mb-2" />
                <p>文件夹中暂无文件，或正在扫描中...</p>
              </div>
            ) : (
              <div className="space-y-2">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 cursor-pointer"
                    onClick={() => { setSelectedFile(file); setShowFileDetail(true); }}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <File className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{file.file_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {file.file_extension}
                          {file.auto_category && ` · ${file.auto_category}`}
                          {file.detected_at && ` · ${new Date(file.detected_at).toLocaleDateString('zh-CN')}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {file.status === 'processing' && (
                        <Badge variant="secondary" className="text-xs">
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                          识别中
                        </Badge>
                      )}
                      {file.status === 'pending' && (
                        <Badge variant="outline" className="text-xs">
                          <Clock className="h-3 w-3 mr-1" />
                          等待中
                        </Badge>
                      )}
                      {file.status !== 'processing' && file.status !== 'pending' && (
                        <StatusBadge status={file.status} />
                      )}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7"
                        onClick={(e) => { e.stopPropagation(); reprocessMutation.mutate(file.id); }}
                        disabled={reprocessMutation.isPending}
                      >
                        <RotateCw className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-red-500"
                        onClick={(e) => { e.stopPropagation(); deleteFileMutation.mutate(file.id); }}
                        disabled={deleteFileMutation.isPending}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color = 'text-muted-foreground' }: {
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

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
    completed: { label: '已完成', variant: 'default' },
    processing: { label: '处理中', variant: 'secondary' },
    pending: { label: '待处理', variant: 'outline' },
    failed: { label: '失败', variant: 'destructive' },
    skipped: { label: '已跳过', variant: 'secondary' },
  };
  const c = config[status] || { label: status, variant: 'secondary' };
  return <Badge variant={c.variant} className="text-xs">{c.label}</Badge>;
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function folderRecentFileToRecord(file: FolderStatus['recent_files'][number]): FolderFileRecord {
  return {
    id: file.id,
    file_name: file.file_name,
    file_extension: file.file_name.split('.').pop() || '',
    file_size: null,
    auto_category: file.auto_category,
    auto_summary: null,
    status: file.status,
    error_message: file.error_message,
    evidence_id: file.evidence_id,
    processed_at: file.processed_at,
    detected_at: file.processed_at || '',
  };
}

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || fallback;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}
