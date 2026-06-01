import { useQuery } from '@tanstack/react-query';
import { ClipboardCheck, FileDown } from 'lucide-react';
import axiosInstance from '@/api/client';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface DocumentExportAudit {
  id: number;
  user_id?: string | null;
  export_action: string;
  export_format: string;
  checked_items: string[];
  checked_item_count: number;
  confirmed_at?: string | null;
}

interface AuditResponse {
  audits: DocumentExportAudit[];
  total: number;
}

interface Props {
  documentId?: string | number | null;
  compact?: boolean;
}

const ACTION_LABELS: Record<string, string> = {
  download: '文书下载',
  markdown: 'Markdown 导出',
  'evidence-book': '证据册下载',
};

const CHECK_ITEM_LABELS: Record<string, string> = {
  parties: '当事人',
  claims: '请求/金额',
  facts: '事实依据',
  evidence: '证据目录',
  law: '法条案例',
  signature: '签章后果',
};

function formatDate(value?: string | null) {
  if (!value) return '未记录时间';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function DocumentExportAuditHistory({ documentId, compact = false }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['document-export-review-audits', documentId],
    queryFn: () =>
      axiosInstance
        .get<AuditResponse>(`/api/documents/${documentId}/export-review-audits`)
        .then((res) => res.data),
    enabled: !!documentId,
  });

  if (!documentId) return null;

  const audits = data?.audits || [];
  const latest = audits[0];

  return (
    <Card className={compact ? 'border-dashed' : ''}>
      <CardHeader className={compact ? 'pb-2' : undefined}>
        <CardTitle className="flex items-center gap-2 text-base">
          <ClipboardCheck className="h-4 w-4 text-primary" />
          导出核验记录
          {latest && <Badge variant="outline">{data?.total || audits.length} 次</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className={compact ? 'space-y-2 pt-0' : 'space-y-3'}>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">正在读取核验记录...</p>
        ) : audits.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无导出核验记录。</p>
        ) : (
          audits.slice(0, compact ? 2 : 5).map((audit) => (
            <div key={audit.id} className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 font-medium">
                  <FileDown className="h-4 w-4 text-muted-foreground" />
                  {ACTION_LABELS[audit.export_action] || audit.export_action}
                  <Badge variant="secondary">{audit.export_format.toUpperCase()}</Badge>
                </div>
                <span className="text-xs text-muted-foreground">{formatDate(audit.confirmed_at)}</span>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {(audit.checked_items || []).map((item) => (
                  <Badge key={item} variant="outline" className="text-xs">
                    {CHECK_ITEM_LABELS[item] || item}
                  </Badge>
                ))}
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                核验人：{audit.user_id || '未记录'}，已确认 {audit.checked_item_count} 项
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
