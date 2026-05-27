const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
  const dir = path.dirname(fullPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(fullPath, content, 'utf-8');
  console.log('Fixed:', relPath);
}

// Fix adversarial-panel.tsx
writeFile('components/adversarial/adversarial-panel.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function AdversarialPanel({ caseId }: Props) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">对抗性分析</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />新建分析</Button>
      </div>
      <Card>
        <CardHeader><CardTitle>四象限分析</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border p-4"><h4 className="font-medium text-green-600">我方优势</h4><p className="text-sm text-muted-foreground mt-2">暂无数据</p></div>
            <div className="rounded-lg border p-4"><h4 className="font-medium text-red-600">我方劣势</h4><p className="text-sm text-muted-foreground mt-2">暂无数据</p></div>
            <div className="rounded-lg border p-4"><h4 className="font-medium text-amber-600">对方劣势</h4><p className="text-sm text-muted-foreground mt-2">暂无数据</p></div>
            <div className="rounded-lg border p-4"><h4 className="font-medium text-blue-600">对方优势</h4><p className="text-sm text-muted-foreground mt-2">暂无数据</p></div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
`);

// Fix hearing-import.tsx
writeFile('components/adversarial/hearing-import.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

interface Props { caseId: string; onImport: () => void; }

export function HearingImport({ caseId, onImport }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>导入到庭审</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">将对抗性分析结果导入到出庭抗辩模块</p>
        <Button onClick={onImport}><FileText className="mr-2 h-4 w-4" />导入</Button>
      </CardContent>
    </Card>
  );
}
`);

// Fix issue-manager.tsx
writeFile('components/adversarial/issue-manager.tsx', `import { Button } from '@/components/ui/button';
import { IssueCard } from './issue-card';
import { Plus } from 'lucide-react';

interface Props { caseId: string; issues: any[]; isLoading: boolean; onAdd: () => void; onSelect: (issue: any) => void; }

export function IssueManager({ caseId, issues, isLoading, onAdd, onSelect }: Props) {
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
`);

// Fix appeal-argument.tsx
writeFile('components/appeal/appeal-argument.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

interface Props { arguments: any[]; isLoading: boolean; onAdd: () => void; }

export function AppealArgumentList({ arguments: args, isLoading, onAdd }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-20 rounded bg-muted" /></div>;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">上诉论证</h3>
        <Button size="sm" onClick={onAdd}><Plus className="mr-2 h-4 w-4" />添加论证</Button>
      </div>
      {!args?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无论证点</p>
      ) : (
        <div className="space-y-3">
          {args.map((a: any) => (
            <Card key={a.id}>
              <CardContent className="p-4">
                <p className="font-medium">{a.title}</p>
                <p className="text-sm text-muted-foreground">{a.type} · 成功率: {a.successProbability}%</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
`);

// Fix appeal-doc-generator.tsx
writeFile('components/appeal/appeal-doc-generator.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

interface Props { caseId: string; onGenerate: (type: string) => void; }

export function AppealDocGenerator({ caseId, onGenerate }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>上诉文书生成</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full" onClick={() => onGenerate('上诉状')}><FileText className="mr-2 h-4 w-4" />生成上诉状</Button>
        <Button className="w-full" variant="outline" onClick={() => onGenerate('答辩意见')}><FileText className="mr-2 h-4 w-4" />生成答辩意见</Button>
        <Button className="w-full" variant="outline" onClick={() => onGenerate('新证据清单')}><FileText className="mr-2 h-4 w-4" />生成新证据清单</Button>
      </CardContent>
    </Card>
  );
}
`);

// Fix appeal-overview.tsx
writeFile('components/appeal/appeal-overview.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAppealList } from '@/hooks/use-appeal';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function AppealOverview({ caseId }: Props) {
  const { data, isLoading } = useAppealList(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">上诉追踪</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />新建上诉</Button>
      </div>
      {!data?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无上诉记录</p>
      ) : (
        <div className="space-y-3">
          {data.map((a: any) => (
            <Card key={a.id}><CardContent className="p-4"><p className="font-medium">{a.originalCourt}</p><p className="text-sm text-muted-foreground">上诉期限: {a.appealDeadline} · 状态: {a.status}</p></CardContent></Card>
          ))}
        </div>
      )}
    </div>
  );
}
`);

// Fix letter-card.tsx
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

// Fix reminder-card.tsx
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

// Fix report-card.tsx
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

// Fix confirm-dialog.tsx
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

// Fix document-version.tsx
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

// Fix version-diff.tsx
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

// Fix case-template-card.tsx
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

// Fix case-overview.tsx
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

console.log('All common components fixed!');
