import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useEvidenceList, useUploadEvidence } from '@/hooks/use-evidence';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Button } from '@/components/ui/button';
import { Plus, FileCheck, Loader2 } from 'lucide-react';
import { useRef } from 'react';
import { toast } from 'sonner';
import type { Evidence } from '@/types/evidence.types';

const UPLOAD_STEPS = [
  '正在上传文件...',
  '正在解析文件内容...',
  '正在识别文字（OCR）...',
  '正在分析证据类型...',
  '正在提取关键信息...',
  '正在评估证据证明力参考...',
  '正在生成规范名称...',
  '即将完成...',
];

interface Props { caseId: string; }

type EvidenceListItem = Evidence & {
  display_name?: string;
  original_filename?: string;
  evidence_type?: string;
  source_party?: string;
  proves_facts?: Array<string | { fact?: string }>;
  credibility_score?: number;
};

export function EvidenceList({ caseId }: Props) {
  const { data, isLoading, isError, refetch } = useEvidenceList(caseId);
  const upload = useUploadEvidence(caseId);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStep, setUploadStep] = useState(0);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (!upload.isPending) {
      setUploadStep(0);
      setUploadProgress(0);
      return;
    }
    setUploadStep(0);
    setUploadProgress(0);

    const stepInterval = setInterval(() => {
      setUploadStep((prev) => Math.min(prev + 1, UPLOAD_STEPS.length - 1));
    }, 4000);

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        const next = prev + (prev < 20 ? 5 : prev < 50 ? 3 : prev < 80 ? 2 : 1);
        return Math.min(next, 95);
      });
    }, 500);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
    };
  }, [upload.isPending]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    upload.mutate(formData, {
      onSuccess: () => {
        toast.success(`成功上传 ${files.length} 个文件`);
        refetch();
      },
      onError: () => {
        toast.error('上传失败');
      },
    });
    e.target.value = '';
  };

  if (isLoading) return <PageSkeleton />;
  if (isError) return <EmptyState title="加载失败" description="证据数据获取失败" actionLabel="重试" onAction={() => refetch()} />;
  if (!data?.length) return (
    <EmptyState
      title="暂无证据"
      description="上传第一份证据开始"
      actionLabel="上传证据"
      onAction={handleUploadClick}
    />
  );

  const evidenceItems = data as EvidenceListItem[];

  return (
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileChange}
        accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.xlsx,.xls"
      />
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">证据列表 ({data.length})</h2>
        <div className="flex gap-2">
          <Button size="sm" onClick={handleUploadClick} disabled={upload.isPending}>
            {upload.isPending ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />处理中...</>
            ) : (
              <><Plus className="mr-2 h-4 w-4" />上传证据</>
            )}
          </Button>
        </div>
      </div>

      {/* Upload progress */}
      {upload.isPending && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm">
              <FileCheck className="h-4 w-4 text-primary" />
              <span className="font-medium text-primary">{UPLOAD_STEPS[uploadStep]}</span>
            </div>
            <Progress value={uploadProgress} className="mt-2 h-1.5" />
            <p className="mt-1 text-xs text-muted-foreground">AI 正在分析证据内容，请稍候...</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {evidenceItems.map((e) => (
          <Card key={e.id}>
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base leading-tight" title={e.display_name || e.original_filename || '未命名证据'}>
                  {e.display_name || e.original_filename || '未命名证据'}
                </CardTitle>
                {e.original_filename && e.display_name && e.display_name !== e.original_filename && (
                  <span className="shrink-0 text-xs text-muted-foreground" title={`原始文件: ${e.original_filename}`}>
                    原: {e.original_filename.length > 15 ? e.original_filename.substring(0, 15) + '...' : e.original_filename}
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{e.evidence_type || e.type || '其他'} · {e.source_party || e.source || '未知'}</p>
              {e.proves_facts && e.proves_facts.length > 0 && (
                <p className="text-xs mt-1 text-muted-foreground">
                  证明: {typeof e.proves_facts[0] === 'string' ? e.proves_facts[0] : (e.proves_facts[0]?.fact || '')}
                </p>
              )}
              {(e.credibility_score != null || e.credibilityScore != null) && (
                <p className="text-sm mt-1">证明力参考: {e.credibility_score ?? e.credibilityScore}%</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
