const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
  const dir = path.dirname(fullPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(fullPath, content, 'utf-8');
}

// Fix all stub components that have JSX syntax errors
// These are placeholder components - they just render a simple UI

writeFile('components/appeal/appeal-countdown.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { AlertTriangle } from 'lucide-react';
interface Props { deadline: string; daysRemaining: number; }
export function AppealCountdown({ deadline, daysRemaining }: Props) {
  const isUrgent = daysRemaining <= 7;
  return (
    <Card className={isUrgent ? 'border-red-500' : ''}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          {isUrgent && <AlertTriangle className="h-5 w-5 text-red-500" />}
          <div>
            <p className="text-sm text-muted-foreground">上诉期限</p>
            <p className="text-2xl font-bold">{daysRemaining} 天</p>
            <p className="text-xs text-muted-foreground">{deadline}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/appeal/appeal-argument-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
interface Props { title: string; type: string; successProbability?: number; }
export function AppealArgumentCard({ title, type, successProbability }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="font-medium">{title}</p>
        <p className="text-sm text-muted-foreground">{type}</p>
        {successProbability != null && (
          <div className="mt-2">
            <Progress value={successProbability} />
            <p className="text-xs text-muted-foreground mt-1">成功率: {successProbability}%</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/appeal/appeal-milestone.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Circle } from 'lucide-react';
const MILESTONES = ['递交上诉状', '缴纳上诉费', '提交答辩状', '二审开庭', '二审判决'];
interface Props { completedCount: number; }
export function AppealMilestone({ completedCount }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>上诉里程碑</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {MILESTONES.map((m, i) => (
          <div key={m} className="flex items-center gap-3">
            {i < completedCount ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
            <span className={i < completedCount ? 'text-green-600' : 'text-muted-foreground'}>{m}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/report-card.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
interface Props { title: string; type: string; status: string; createdAt: string; onView: () => void; onExport: () => void; }
export function ReportCard({ title, type, status, createdAt, onView, onExport }: Props) {
  const statusMap: Record<string, string> = { generating: 'default', completed: 'default', failed: 'destructive' };
  const statusLabel: Record<string, string> = { generating: '生成中', completed: '已完成', failed: '失败' };
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          <Badge variant={(statusMap[status] || 'secondary') as 'default'}>{statusLabel[status] || status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{type} · {createdAt}</p>
        <div className="mt-2 flex gap-2">
          {status === 'completed' && (
            <>
              <button onClick={onView} className="text-sm text-primary hover:underline">查看</button>
              <button onClick={onExport} className="text-sm text-primary hover:underline">导出</button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/confirm-dialog.tsx', `import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
interface Props { open: boolean; onOpenChange: (open: boolean) => void; title: string; description: string; confirmLabel?: string; cancelLabel?: string; variant?: 'default' | 'destructive'; isLoading?: boolean; onConfirm: () => void; }
export function ConfirmDialog({ open, onOpenChange, title, description, confirmLabel = '确认', cancelLabel = '取消', variant = 'default', isLoading, onConfirm }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>{cancelLabel}</Button>
          <Button variant={variant === 'destructive' ? 'destructive' : 'default'} onClick={onConfirm} disabled={isLoading}>
            {isLoading ? '处理中...' : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
`);

writeFile('components/common/document-version.tsx', `import { Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
interface Props { version: number; timestamp: string; isCurrent?: boolean; onSelect: () => void; onCompare?: () => void; }
export function DocumentVersion({ version, timestamp, isCurrent, onSelect, onCompare }: Props) {
  return (
    <Card className={isCurrent ? 'border-primary' : 'cursor-pointer hover:shadow-md'} onClick={onSelect}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">v{version}</span>
          </div>
          {isCurrent && <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">当前</span>}
        </div>
        <p className="text-xs text-muted-foreground mt-2">{timestamp}</p>
        {onCompare && !isCurrent && <button onClick={(e) => { e.stopPropagation(); onCompare(); }} className="mt-2 text-xs text-primary hover:underline">对比当前版本</button>}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/version-diff.tsx', `interface Props { oldContent: string; newContent: string; }
export function VersionDiff({ oldContent, newContent }: Props) {
  const oldLines = oldContent.split('\\n');
  const newLines = newContent.split('\\n');
  const maxLines = Math.max(oldLines.length, newLines.length);
  const diff: { type: string; oldLine?: string; newLine?: string }[] = [];
  for (let i = 0; i < maxLines; i++) {
    if (oldLines[i] === newLines[i]) {
      diff.push({ type: 'same', oldLine: oldLines[i], newLine: newLines[i] });
    } else {
      if (oldLines[i]) diff.push({ type: 'removed', oldLine: oldLines[i] });
      if (newLines[i]) diff.push({ type: 'added', newLine: newLines[i] });
    }
  }
  return (
    <div className="rounded-md border font-mono text-sm">
      {diff.map((line, i) => (
        <div key={i} className={\`flex px-3 py-1 \${line.type === 'added' ? 'bg-green-50 dark:bg-green-900/20' : line.type === 'removed' ? 'bg-red-50 dark:bg-red-900/20' : ''}\`}>
          <span className="w-8 shrink-0 text-muted-foreground">{i + 1}</span>
          <span className={line.type === 'added' ? 'text-green-700 dark:text-green-400' : line.type === 'removed' ? 'text-red-700 dark:text-red-400' : ''}>
            {line.type === 'added' ? '+ ' : line.type === 'removed' ? '- ' : '  '}
            {line.newLine || line.oldLine}
          </span>
        </div>
      ))}
    </div>
  );
}
`);

writeFile('components/common/reminder-card.tsx', `import { Bell } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';
interface Props { title: string; caseTitle: string; type: string; dueDate?: string; isRead: boolean; priority: 'high' | 'medium' | 'low'; onClick: () => void; onMarkRead: () => void; }
export function ReminderCard({ title, caseTitle, type, dueDate, isRead, priority, onClick, onMarkRead }: Props) {
  const priorityColors: Record<string, string> = { high: 'border-l-red-500', medium: 'border-l-amber-500', low: 'border-l-green-500' };
  return (
    <div className={\`rounded-lg border border-l-4 \${priorityColors[priority]} bg-card p-4 \${!isRead ? 'font-medium' : ''}\`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2"><Bell className="h-4 w-4 text-muted-foreground" /><span>{title}</span></div>
          <p className="mt-1 text-sm text-muted-foreground">{caseTitle}</p>
          {dueDate && <p className="mt-1 text-xs text-muted-foreground">截止: {formatChineseDate(dueDate)}</p>}
        </div>
        <div className="flex gap-2">
          <button onClick={onClick} className="text-sm text-primary hover:underline">查看</button>
          {!isRead && <button onClick={onMarkRead} className="text-sm text-muted-foreground hover:underline">标记已读</button>}
        </div>
      </div>
    </div>
  );
}
`);

writeFile('components/common/letter-card.tsx', `import { Mail } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatChineseDate } from '@/lib/date';
interface Props { title: string; type: string; category: string; mailStatus: string; createdAt: string; replyReceived?: boolean; onClick: () => void; }
export function LetterCard({ title, type, category, mailStatus, createdAt, replyReceived, onClick }: Props) {
  const statusLabels: Record<string, string> = { draft: '草稿', sending: '发送中', sent: '已发送', delivered: '已送达', read: '已阅读', replied: '已回复' };
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base"><Mail className="h-4 w-4" />{title}</CardTitle>
          <div className="flex gap-2">
            <Badge variant="secondary">{statusLabels[mailStatus] || mailStatus}</Badge>
            {replyReceived && <Badge variant="default">已回复</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{category} · {formatChineseDate(createdAt)}</p>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/case-template-card.tsx', `import { FileText } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
interface Props { type: string; label: string; fields: string[]; evidence: string[]; documents: string[]; onSelect: () => void; }
export function CaseTemplateCard({ label, fields, evidence, documents, onSelect }: Props) {
  return (
    <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={onSelect}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">{label}</h3>
        </div>
        <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
          <li>预填字段: {fields.join(', ')}</li>
          <li>推荐证据: {evidence.slice(0, 2).join(', ')}...</li>
          <li>推荐文书: {documents.join(', ')}</li>
        </ul>
        <button className="mt-3 w-full rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90">选择</button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/dashboard/case-overview.tsx', `import { DataStat } from '@/components/common/data-stat';
import { useDashboard } from '@/api/dashboard.api';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
export function CaseOverview() {
  const { data, isLoading, isError } = useDashboard();
  if (isLoading) return <PageSkeleton />;
  if (isError) return <EmptyState title="加载失败" description="请检查网络连接" />;
  const stats = data?.caseStats;
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <DataStat label="全案件数" value={stats?.total || 0} />
      <DataStat label="进行中" value={stats?.inProgress || 0} />
      <DataStat label="本月新增" value={stats?.newThisMonth || 0} />
      <DataStat label="执行中" value={stats?.inExecution || 0} />
    </div>
  );
}
`);

writeFile('components/evidence/evidence-graph.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
interface Props { caseId: string; }
export function EvidenceGraph({ caseId }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>证据图谱</CardTitle></CardHeader>
      <CardContent>
        <div className="h-[400px] flex items-center justify-center rounded-lg border bg-muted/20">
          <p className="text-muted-foreground">证据图谱可视化区域</p>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-uploader.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';
interface Props { caseId: string; onUpload: (file: File) => void; }
export function EvidenceUploader({ caseId, onUpload }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>上传证据</CardTitle></CardHeader>
      <CardContent>
        <div className="border-2 border-dashed rounded-lg p-8 text-center">
          <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">拖拽文件到此处或点击上传</p>
          <Button className="mt-4">选择文件</Button>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-relate.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'lucide-react';
interface Props { evidenceId: string; onRelate: (targetId: string) => void; }
export function EvidenceRelate({ evidenceId, onRelate }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>关联管理</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2"><Link className="h-4 w-4 text-muted-foreground" /><span className="text-sm">关联到文书/争点</span></div>
        <Button size="sm">添加关联</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-annotation.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
interface Props { evidenceId: string; annotations: { text: string; page: number }[]; }
export function EvidenceAnnotation({ evidenceId, annotations }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>批注</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {annotations.map((a, i) => (
          <div key={i} className="p-2 rounded bg-muted">
            <p className="text-sm">{a.text}</p>
            <p className="text-xs text-muted-foreground">第 {a.page} 页</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-analysis-chat.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
interface Props { evidenceId: string; }
export function EvidenceAnalysisChat({ evidenceId }: Props) {
  const [question, setQuestion] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>证据分析对话</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="h-64 overflow-y-auto rounded border p-4"><p className="text-sm text-muted-foreground">询问关于此证据的问题...</p></div>
        <div className="flex gap-2"><Textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入问题..." className="flex-1" /><Button>发送</Button></div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/correction-form.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
interface Props { evidenceId: string; onSubmit: (corrections: Record<string, string>) => void; }
export function CorrectionForm({ evidenceId, onSubmit }: Props) {
  const [type, setType] = useState('');
  const [proofDirection, setProofDirection] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>人工纠偏</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><Label>证据类型</Label><Input value={type} onChange={(e) => setType(e.target.value)} placeholder="修正类型" /></div>
        <div><Label>证明方向</Label><Input value={proofDirection} onChange={(e) => setProofDirection(e.target.value)} placeholder="修正证明方向" /></div>
        <Button onClick={() => onSubmit({ type, proofDirection })}>提交纠偏</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/hearing/real-time-analysis.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mic, Square } from 'lucide-react';
interface Props { caseId: string; }
export function RealTimeAnalysis({ caseId }: Props) {
  const [isListening, setIsListening] = useState(false);
  return (
    <Card>
      <CardHeader><CardTitle>实时分析</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-center">
          <Button onClick={() => setIsListening(!isListening)} variant={isListening ? 'destructive' : 'default'}>
            {isListening ? <><Square className="mr-2 h-4 w-4" />停止</> : <><Mic className="mr-2 h-4 w-4" />开始监听</>}
          </Button>
        </div>
        {isListening && <div className="h-32 rounded border p-4 overflow-y-auto"><p className="text-sm text-muted-foreground">监听中...</p></div>}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/layout/panel-layout.tsx', `import { useState } from 'react';
interface Props { left: React.ReactNode; right: React.ReactNode; }
export function PanelLayout({ left, right }: Props) {
  const [split, setSplit] = useState(50);
  return (
    <div className="flex h-full">
      <div style={{ width: split + '%' }} className="overflow-y-auto border-r">{left}</div>
      <div className="w-2 bg-border cursor-col-resize" />
      <div style={{ width: (100 - split) + '%' }} className="overflow-y-auto">{right}</div>
    </div>
  );
}
`);

writeFile('components/meeting/audio-player.tsx', `import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, Pause } from 'lucide-react';
interface Props { src: string; }
export function AudioPlayer({ src }: Props) {
  const [isPlaying, setIsPlaying] = useState(false);
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <Button size="icon" onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <div className="flex-1 h-2 bg-muted rounded"><div className="h-2 bg-primary rounded" style={{ width: '30%' }} /></div>
          <span className="text-xs text-muted-foreground">00:00 / 00:00</span>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/meeting/meeting-recorder.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mic, Square } from 'lucide-react';
interface Props { caseId: string; }
export function MeetingRecorder({ caseId }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  return (
    <Card>
      <CardHeader><CardTitle>会议谈判</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-center">
          <Button onClick={() => setIsRecording(!isRecording)} variant={isRecording ? 'destructive' : 'default'}>
            {isRecording ? <><Square className="mr-2 h-4 w-4" />停止录音</> : <><Mic className="mr-2 h-4 w-4" />开始录音</>}
          </Button>
        </div>
        {isRecording && <p className="text-center text-sm text-muted-foreground">录音中...</p>}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-guide.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useEvidenceGuideHook } from '@/hooks/use-evidence-guide';
interface Props { caseId: string; }
export function EvidenceGuide({ caseId }: Props) {
  const { data, isLoading } = useEvidenceGuideHook(caseId);
  if (isLoading) return <div className="animate-pulse"><div className="h-4 w-full rounded bg-muted" /></div>;
  return (
    <Card>
      <CardHeader><CardTitle>证据引导</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><p className="text-sm text-muted-foreground">证据完整性</p><Progress value={data?.completeness || 0} /><p className="text-sm mt-1">{data?.completeness || 0}%</p></div>
        {data?.gaps?.map((g: any, i: number) => (
          <div key={i} className="p-3 rounded-lg border">
            <p className="font-medium">{g.type}</p>
            <p className="text-sm text-muted-foreground">{g.suggestion}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/profile/knowledge-graph.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
interface Props { caseId: string; }
export function KnowledgeGraph({ caseId }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>知识图谱</CardTitle></CardHeader>
      <CardContent>
        <div className="h-[400px] flex items-center justify-center rounded-lg border bg-muted/20">
          <p className="text-muted-foreground">知识图谱可视化区域</p>
        </div>
      </CardContent>
    </Card>
  );
}
`);

console.log('All stub components fixed!');
