import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { File, RefreshCw, Trash2, Loader2 } from 'lucide-react';
import {
  useFolderFiles,
  useDeleteFileRecord,
  useReprocessFile,
} from '@/api/evidence-folder.api';
import { toast } from 'sonner';

interface FolderFileListProps {
  caseId: string;
}

function getApiErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { detail?: string } } }).response;
  const message = (error as { message?: string }).message;
  return response?.data?.detail || message || fallback;
}

export default function FolderFileList({ caseId }: FolderFileListProps) {
  const caseIdNum = parseInt(caseId, 10);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, refetch } = useFolderFiles(caseIdNum, {
    status: statusFilter === 'all' ? undefined : statusFilter,
    page,
    page_size: pageSize,
  });

  const deleteFile = useDeleteFileRecord(caseIdNum);
  const reprocessFile = useReprocessFile(caseIdNum);

  const handleDelete = async (fileId: number) => {
    try {
      await deleteFile.mutateAsync(fileId);
      toast.success('文件记录已删除');
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, '删除失败'));
    }
  };

  const handleReprocess = async (fileId: number) => {
    try {
      await reprocessFile.mutateAsync(fileId);
      toast.success('已重新提交处理');
      refetch();
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, '重新处理失败'));
    }
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <File className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">文件列表</span>
          {data && (
            <span className="text-xs text-muted-foreground">
              共 {data.total} 个文件
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="状态过滤" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="pending">待处理</SelectItem>
              <SelectItem value="processing">处理中</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
              <SelectItem value="skipped">已跳过</SelectItem>
            </SelectContent>
          </Select>
          <Button size="sm" variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-1 h-4 w-4" />
            刷新
          </Button>
        </div>
      </div>

      {/* 表格 */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : data?.records && data.records.length > 0 ? (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>文件名</TableHead>
                <TableHead className="w-[100px]">类型</TableHead>
                <TableHead className="w-[100px]">大小</TableHead>
                <TableHead className="w-[100px]">分类</TableHead>
                <TableHead className="w-[80px]">状态</TableHead>
                <TableHead className="w-[120px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.records.map((file) => (
                <TableRow key={file.id}>
                  <TableCell>
                    <div className="max-w-[300px] truncate" title={file.file_name}>
                      {file.file_name}
                    </div>
                    {file.error_message && (
                      <div className="mt-1 text-xs text-red-500" title={file.error_message}>
                        {file.error_message && file.error_message.length > 50
                      ? `${file.error_message.substring(0, 50)}...`
                      : file.error_message}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {file.file_extension}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatFileSize(file.file_size ?? 0)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {file.auto_category || '-'}
                  </TableCell>
                  <TableCell>
                    <FileStatusBadge status={file.status} />
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {(file.status === 'failed' || file.status === 'completed') && (
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => handleReprocess(file.id)}
                          disabled={reprocessFile.isPending}
                        >
                          <RefreshCw className="h-3.5 w-3.5" />
                        </Button>
                      )}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-red-500 hover:text-red-700"
                        onClick={() => handleDelete(file.id)}
                        disabled={deleteFile.isPending}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="rounded border border-dashed p-8 text-center text-sm text-muted-foreground">
          <File className="mx-auto mb-2 h-8 w-8 opacity-50" />
          <p>暂无文件记录</p>
        </div>
      )}

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            第 {page} / {totalPages} 页
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              上一页
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
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

function formatFileSize(bytes: number): string {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
