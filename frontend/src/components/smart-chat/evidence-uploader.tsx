import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Upload, X, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import axiosInstance from '@/api/client';

interface EvidenceUploaderProps {
  caseId: number;
  onUploadSuccess?: (evidence: unknown) => void;
  trigger?: React.ReactNode;
}

interface UploadState {
  file: File | null;
  name: string;
  type: string;
  content: string;
  provingFacts: string;
  status: 'idle' | 'uploading' | 'success' | 'error';
  message?: string;
}

const EVIDENCE_TYPES = [
  { value: 'contract', label: '合同协议' },
  { value: 'invoice', label: '票据凭证' },
  { value: 'correspondence', label: '函件沟通' },
  { value: 'communication', label: '通讯记录' },
  { value: 'identification', label: '身份证明' },
  { value: 'witness', label: '证人证言' },
  { value: 'appraisal', label: '鉴定意见' },
  { value: 'video_audio', label: '视听资料' },
  { value: 'other', label: '其他证据' },
];

export function EvidenceUploader({ caseId, onUploadSuccess, trigger }: EvidenceUploaderProps) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<UploadState>({
    file: null,
    name: '',
    type: 'other',
    content: '',
    provingFacts: '',
    status: 'idle',
    message: '',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 更新文件信息
    setState(prev => ({
      ...prev,
      file,
      name: file.name.replace(/\.[^/.]+$/, ''), // 移除扩展名
    }));

    // 如果是文本文件，自动读取内容
    if (file.type.startsWith('text/') || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
      try {
        const content = await file.text();
        setState(prev => ({ ...prev, content }));
      } catch {
        toast.error('文件读取失败');
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && fileInputRef.current) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInputRef.current.files = dataTransfer.files;
      fileInputRef.current.dispatchEvent(new Event('change', { bubbles: true }));
    }
  };

  const handleSubmit = async () => {
    if (!state.content.trim()) {
      toast.error('请输入证据内容');
      return;
    }

    if (!state.name.trim()) {
      toast.error('请输入证据名称');
      return;
    }

    setState(prev => ({ ...prev, status: 'uploading', message: '正在提交证据...' }));

    try {
      const response = await axiosInstance.post(`/api/evidence/submit/${caseId}`, {
        name: state.name,
        evidence_type: state.type,
        content: state.content,
        proof_point: state.provingFacts || '待分析',
      });

      setState(prev => ({
        ...prev,
        status: 'success',
        message: '证据上传成功！',
      }));

      toast.success('证据上传成功');

      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }

      // 2秒后关闭
      setTimeout(() => {
        setOpen(false);
        // 重置状态
        setState({
          file: null,
          name: '',
          type: 'other',
          content: '',
          provingFacts: '',
          status: 'idle',
          message: '',
        });
      }, 1500);
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' &&
        err !== null &&
        'response' in err &&
        typeof (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail ===
          'string'
          ? (err as { response: { data: { detail: string } } }).response.data.detail
          : undefined;
      setState(prev => ({
        ...prev,
        status: 'error',
        message: detail || '上传失败，请重试',
      }));
      toast.error('证据上传失败');
    }
  };

  const defaultTrigger = (
    <Button variant="outline" size="sm" className="h-8 text-xs">
      <Upload className="h-3 w-3 mr-1" />
      上传证据
    </Button>
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        {trigger || defaultTrigger}
      </SheetTrigger>
      <SheetContent side="bottom" className="h-[85vh] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>上传证据</SheetTitle>
          <SheetDescription>
            在此处直接上传证据，无需跳转页面
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-4 mt-4">
          {/* 文件上传区域 */}
          <div
            className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileSelect}
              accept=".txt,.md,.pdf,.doc,.docx,.jpg,.jpeg,.png"
            />
            {state.file ? (
              <div className="flex items-center justify-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium">{state.file.name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    setState(prev => ({ ...prev, file: null }));
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <>
                <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">
                  点击或拖拽文件到此处上传
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  支持 txt, md, pdf, doc, docx, 图片等格式
                </p>
              </>
            )}
          </div>

          {/* 证据名称 */}
          <div>
            <label className="text-sm font-medium mb-1 block">证据名称 *</label>
            <Input
              value={state.name}
              onChange={(e) => setState(prev => ({ ...prev, name: e.target.value }))}
              placeholder="例如：借款合同、转账记录、聊天截图"
            />
          </div>

          {/* 证据类型 */}
          <div>
            <label className="text-sm font-medium mb-1 block">证据类型</label>
            <div className="flex flex-wrap gap-2">
              {EVIDENCE_TYPES.map((t) => (
                <Badge
                  key={t.value}
                  variant={state.type === t.value ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setState(prev => ({ ...prev, type: t.value }))}
                >
                  {t.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* 证明事实 */}
          <div>
            <label className="text-sm font-medium mb-1 block">证明事实（可选）</label>
            <Input
              value={state.provingFacts}
              onChange={(e) => setState(prev => ({ ...prev, provingFacts: e.target.value }))}
              placeholder="简要描述这份证据能证明什么"
            />
          </div>

          {/* 证据内容 */}
          <div>
            <label className="text-sm font-medium mb-1 block">证据内容 *</label>
            <Textarea
              value={state.content}
              onChange={(e) => setState(prev => ({ ...prev, content: e.target.value }))}
              placeholder="粘贴或输入证据内容..."
              rows={10}
              className="text-sm font-mono"
            />
          </div>

          {/* 状态提示 */}
          {state.status !== 'idle' && (
            <div className={`flex items-center gap-2 p-3 rounded-lg ${
              state.status === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-950/20 dark:text-green-400' :
              state.status === 'error' ? 'bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400' :
              'bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-400'
            }`}>
              {state.status === 'uploading' && <Loader2 className="h-4 w-4 animate-spin" />}
              {state.status === 'success' && <CheckCircle className="h-4 w-4" />}
              {state.status === 'error' && <AlertCircle className="h-4 w-4" />}
              <span className="text-sm">{state.message}</span>
            </div>
          )}

          {/* 提交按钮 */}
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => setOpen(false)}
              disabled={state.status === 'uploading'}
            >
              取消
            </Button>
            <Button
              className="flex-1"
              onClick={handleSubmit}
              disabled={state.status === 'uploading' || state.status === 'success'}
            >
              {state.status === 'uploading' ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  上传中...
                </>
              ) : '确认上传'}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default EvidenceUploader;
