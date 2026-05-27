const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
  const dir = path.dirname(fullPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(fullPath, content, 'utf-8');
}

// Fix all remaining broken stub components

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

writeFile('components/adversarial/scenario-prediction.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Scenario { scenario: string; probability: number; description: string; }
interface Props { scenarios: Scenario[]; }

export function ScenarioPrediction({ scenarios }: Props) {
  if (!scenarios?.length) return <p className="text-muted-foreground text-center py-8">暂无预测数据</p>;
  return (
    <Card>
      <CardHeader><CardTitle>情景预测</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {scenarios.map((s, i) => (
          <div key={i}>
            <div className="flex justify-between text-sm mb-1"><span>{s.scenario}</span><span>{s.probability}%</span></div>
            <Progress value={s.probability} />
            <p className="text-xs text-muted-foreground mt-1">{s.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/adversarial/swot-quadrant.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { strengths: string[]; weaknesses: string[]; opponentWeaknesses: string[]; opponentStrengths: string[]; }

export function SwotQuadrant({ strengths, weaknesses, opponentWeaknesses, opponentStrengths }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card><CardHeader><CardTitle className="text-green-600">我方优势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{strengths.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-red-600">我方劣势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{weaknesses.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-amber-600">对方劣势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{opponentWeaknesses.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-blue-600">对方优势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{opponentStrengths.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
    </div>
  );
}
`);

writeFile('components/adversarial/evidence-matrix-table.tsx', `import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface Props { evidence: any[]; issues: any[]; }

export function EvidenceMatrixTable({ evidence, issues }: Props) {
  return (
    <Table>
      <TableHeader><TableRow><TableHead>证据</TableHead>{issues.map((i) => <TableHead key={i.id}>{i.title}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{evidence.map((e) => <TableRow key={e.id}><TableCell>{e.name}</TableCell>{issues.map((i) => <TableCell key={i.id}>-</TableCell>)}</TableRow>)}</TableBody>
    </Table>
  );
}
`);

writeFile('components/adversarial/action-plan.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Circle } from 'lucide-react';

interface Props { actions: string[]; onAction: (action: string) => void; }

export function ActionPlan({ actions, onAction }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>行动计划</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {actions.map((a, i) => (
          <div key={i} className="flex items-center gap-3">
            <Circle className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm flex-1">{a}</span>
            <Button size="sm" variant="outline" onClick={() => onAction(a)}>执行</Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

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

writeFile('components/common/deadline-timeline.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Props { events: { date: string; title: string; type: string }[]; }

export function DeadlineTimeline({ events }: Props) {
  return (
    <Card>
      <CardContent className="p-4 space-y-3">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div>
              <p className="text-sm font-medium">{e.title}</p>
              <p className="text-xs text-muted-foreground">{formatChineseDate(e.date)} · {e.type}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/export-matrix.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface Item { name: string; formats: string[]; }
interface Props { items: Item[]; onExport: (item: string, format: string) => void; }

export function ExportMatrix({ items, onExport }: Props) {
  const formats = ['PDF', 'Word', 'Markdown', 'TXT'];
  return (
    <Card>
      <CardHeader><CardTitle>导出矩阵</CardTitle></CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr><th className="text-left p-2">内容</th>{formats.map((f) => <th key={f} className="p-2">{f}</th>)}</tr></thead>
            <tbody>{items.map((item) => (
              <tr key={item.name} className="border-t">
                <td className="p-2">{item.name}</td>
                {formats.map((f) => <td key={f} className="p-2"><Button size="sm" variant="outline" onClick={() => onExport(item.name, f)}><Download className="h-3 w-3" /></Button></td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/party-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { User } from 'lucide-react';

interface Props { name: string; role: string; phone?: string; onClick: () => void; }

export function PartyCard({ name, role, phone, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <User className="h-5 w-5 text-muted-foreground" />
          <div>
            <p className="font-medium">{name}</p>
            <p className="text-sm text-muted-foreground">{role}{phone ? ' · ' + phone : ''}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/thread-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { ListTodo } from 'lucide-react';

interface Props { title: string; status: string; priority: string; onClick: () => void; }

export function ThreadCard({ title, status, priority, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <ListTodo className="h-4 w-4 text-muted-foreground" />
          <p className="font-medium">{title}</p>
        </div>
        <p className="text-sm text-muted-foreground mt-1">{status} · {priority}</p>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/toast-notification.tsx', `import { toast } from 'sonner';

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  if (type === 'success') toast.success(message);
  else if (type === 'error') toast.error(message);
  else toast.info(message);
}
`);

writeFile('components/common/print-layout.tsx', `import React from 'react';

interface Props { children: React.ReactNode; }

export function PrintLayout({ children }: Props) {
  return <div className="print:p-8 print:bg-white">{children}</div>;
}
`);

writeFile('components/common/counter-claim-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { Scale } from 'lucide-react';

interface Props { title: string; status: string; amount?: number; onClick: () => void; }

export function CounterClaimCard({ title, status, amount, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-muted-foreground" />
          <p className="font-medium">{title}</p>
        </div>
        <p className="text-sm text-muted-foreground mt-1">{status}{amount != null ? ' · ¥' + amount.toLocaleString() : ''}</p>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/common/cross-exam-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { Gavel } from 'lucide-react';

interface Props { evidenceName: string; authenticity: string; legality: string; relevance: string; }

export function CrossExamCard({ evidenceName, authenticity, legality, relevance }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Gavel className="h-4 w-4 text-muted-foreground" />
          <p className="font-medium">{evidenceName}</p>
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
          <div>真实性: {authenticity}</div>
          <div>合法性: {legality}</div>
          <div>关联性: {relevance}</div>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/document/document-editor.tsx', `import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { AutoSaveIndicator } from '@/components/common/auto-save-indicator';

interface Props { content: string; onSave: (content: string) => void; }

export function DocumentEditor({ content, onSave }: Props) {
  const [text, setText] = useState(content);
  return (
    <div className="space-y-4">
      <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={20} className="font-mono" />
      <div className="flex justify-between items-center">
        <AutoSaveIndicator status="saved" lastSaved={new Date()} />
        <Button onClick={() => onSave(text)}>保存</Button>
      </div>
    </div>
  );
}
`);

writeFile('components/document/document-preview.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { title: string; content: string; }

export function DocumentPreview({ title, content }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent><div className="prose max-w-none whitespace-pre-wrap">{content}</div></CardContent>
    </Card>
  );
}
`);

writeFile('components/document/document-suggestions.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lightbulb } from 'lucide-react';

interface Suggestion { type: string; reason: string; }
interface Props { suggestions: Suggestion[]; onGenerate: (type: string) => void; }

export function DocumentSuggestions({ suggestions, onGenerate }: Props) {
  if (!suggestions?.length) return null;
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><Lightbulb className="h-5 w-5 text-amber-500" />AI 推荐文书</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {suggestions.map((s, i) => (
          <div key={i} className="flex justify-between items-center p-3 rounded-lg border">
            <div><p className="font-medium">{s.type}</p><p className="text-sm text-muted-foreground">{s.reason}</p></div>
            <Button size="sm" onClick={() => onGenerate(s.type)}>生成</Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/document/document-version-panel.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DocumentVersion } from '@/components/common/document-version';

interface Version { version: number; timestamp: string; }
interface Props { versions: Version[]; currentVersion: number; onSelect: (v: number) => void; onCompare: (v: number) => void; }

export function DocumentVersionPanel({ versions, currentVersion, onSelect, onCompare }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>版本历史</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {versions.map((v) => (
          <DocumentVersion key={v.version} version={v.version} timestamp={v.timestamp} isCurrent={v.version === currentVersion} onSelect={() => onSelect(v.version)} onCompare={() => onCompare(v.version)} />
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/document/template-grid.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { FileText } from 'lucide-react';

interface Template { id: string; name: string; category: string; }
interface Props { templates: Template[]; onSelect: (id: string) => void; }

export function TemplateGrid({ templates, onSelect }: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {templates.map((t) => (
        <Card key={t.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(t.id)}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <div><p className="font-medium">{t.name}</p><p className="text-sm text-muted-foreground">{t.category}</p></div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
`);

writeFile('components/document/template-selector.tsx', `import { useState } from 'react';
import { TemplateGrid } from './template-grid';

interface Template { id: string; name: string; category: string; }
interface Props { templates: Template[]; onSelect: (id: string) => void; }

export function TemplateSelector({ templates, onSelect }: Props) {
  const [category, setCategory] = useState('all');
  const filtered = category === 'all' ? templates : templates.filter((t) => t.category === category);
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button onClick={() => setCategory('all')} className="px-3 py-1 rounded-md text-sm bg-primary text-primary-foreground">全部</button>
        <button onClick={() => setCategory('诉讼')} className="px-3 py-1 rounded-md text-sm border">诉讼</button>
        <button onClick={() => setCategory('非诉')} className="px-3 py-1 rounded-md text-sm border">非诉</button>
      </div>
      <TemplateGrid templates={filtered} onSelect={onSelect} />
    </div>
  );
}
`);

writeFile('components/document/document-list.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDocumentList } from '@/hooks/use-document';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function DocumentList({ caseId }: Props) {
  const { data, isLoading } = useDocumentList(caseId);
  if (isLoading) return <PageSkeleton />;
  if (!data?.length) return <EmptyState title="暂无文书" description="生成第一份文书" actionLabel="生成文书" onAction={() => {}} />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">文书列表 ({data.length})</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />新建文书</Button></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.map((d: any) => (<Card key={d.id}><CardHeader className="pb-2"><CardTitle className="text-base">{d.title}</CardTitle></CardHeader><CardContent><p className="text-sm text-muted-foreground">{d.type} · v{d.version}</p></CardContent></Card>))}</div>
    </div>
  );
}
`);

writeFile('components/document/document-generator.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useGenerateDocument } from '@/hooks/use-document';

interface Props { caseId: string; }

export function DocumentGenerator({ caseId }: Props) {
  const [prompt, setPrompt] = useState('');
  const generate = useGenerateDocument();
  const handleGenerate = () => { generate.mutate({ caseId, data: { type: 'custom', prompt } }); };
  return (
    <Card>
      <CardHeader><CardTitle>文书生成</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="描述您需要生成的文书..." rows={4} />
        <Button onClick={handleGenerate} disabled={generate.isPending}>{generate.isPending ? '生成中...' : '生成文书'}</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-list.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEvidenceList } from '@/hooks/use-evidence';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function EvidenceList({ caseId }: Props) {
  const { data, isLoading } = useEvidenceList(caseId);
  if (isLoading) return <PageSkeleton />;
  if (!data?.length) return <EmptyState title="暂无证据" description="上传第一份证据开始" actionLabel="上传证据" onAction={() => {}} />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">证据列表 ({data.length})</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />上传证据</Button></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.map((e: any) => (<Card key={e.id}><CardHeader className="pb-2"><CardTitle className="text-base">{e.name}</CardTitle></CardHeader><CardContent><p className="text-sm text-muted-foreground">{e.type} · {e.source}</p>{e.credibilityScore != null && <p className="text-sm mt-1">信度: {e.credibilityScore}%</p>}</CardContent></Card>))}</div>
    </div>
  );
}
`);

writeFile('components/evidence/evidence-detail.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Evidence { id: string; name: string; type: string; source: string; credibilityScore?: number; description?: string; }
interface Props { evidence: Evidence; }

export function EvidenceDetail({ evidence }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>{evidence.name}</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div><p className="text-sm text-muted-foreground">类型</p><p>{evidence.type}</p></div>
        <div><p className="text-sm text-muted-foreground">来源</p><p>{evidence.source}</p></div>
        {evidence.credibilityScore != null && <div><p className="text-sm text-muted-foreground">信度评分</p><p>{evidence.credibilityScore}%</p></div>}
        {evidence.description && <div><p className="text-sm text-muted-foreground">描述</p><p>{evidence.description}</p></div>}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-matrix.tsx', `import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface Props { evidence: any[]; issues: any[]; }

export function EvidenceMatrix({ evidence, issues }: Props) {
  return (
    <Table>
      <TableHeader><TableRow><TableHead>证据</TableHead>{issues.map((i) => <TableHead key={i.id}>{i.title}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{evidence.map((e) => <TableRow key={e.id}><TableCell>{e.name}</TableCell>{issues.map((i) => <TableCell key={i.id}>-</TableCell>)}</TableRow>)}</TableBody>
    </Table>
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

writeFile('components/evidence/evidence-timeline.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Item { name: string; createdAt: string; }
interface Props { evidence: Item[]; }

export function EvidenceTimeline({ evidence }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>证据时间轴</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {evidence.map((e, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div><p className="text-sm font-medium">{e.name}</p><p className="text-xs text-muted-foreground">{formatChineseDate(e.createdAt)}</p></div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/evidence-type-badge.tsx', `import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const evidenceTypeVariants = cva('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', {
  variants: {
    type: {
      contract: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      receipt: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      letter: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      identity: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      communication: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
      witness: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      expert: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
      audio_video: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      other: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    },
  },
  defaultVariants: { type: 'other' },
});

interface Props extends VariantProps<typeof evidenceTypeVariants> { label: string; }

export function EvidenceTypeBadge({ label, type }: Props) {
  return <span className={cn(evidenceTypeVariants({ type }))}>{label}</span>;
}
`);

writeFile('components/evidence/evidence-annotation.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Annotation { text: string; page: number; }
interface Props { evidenceId: string; annotations: Annotation[]; }

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

writeFile('components/evidence/completeness-check.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useEvidenceCompleteness } from '@/hooks/use-evidence';

interface Props { caseId: string; }

export function CompletenessCheck({ caseId }: Props) {
  const { data, isLoading } = useEvidenceCompleteness(caseId);
  if (isLoading) return <div className="animate-pulse"><div className="h-4 w-full rounded bg-muted" /></div>;
  return (
    <Card>
      <CardHeader><CardTitle>证据完整性检查</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Progress value={data?.completeness || 0} />
        <p className="text-sm text-center">{data?.completeness || 0}% 完整</p>
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

writeFile('components/evidence/credibility-score.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Dimension { name: string; score: number; }
interface Props { score: number; dimensions: Dimension[]; }

export function CredibilityScore({ score, dimensions }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>信度评分</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center"><p className="text-3xl font-bold">{score}%</p><Progress value={score} className="mt-2" /></div>
        <div className="space-y-2">
          {dimensions.map((d, i) => (
            <div key={i}>
              <div className="flex justify-between text-sm"><span>{d.name}</span><span>{d.score}%</span></div>
              <Progress value={d.score} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/evidence/duplicate-detector.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy } from 'lucide-react';

interface Duplicate { id: string; name: string; similarity: number; }
interface Props { duplicates: Duplicate[]; onMerge: (ids: string[]) => void; }

export function DuplicateDetector({ duplicates, onMerge }: Props) {
  if (!duplicates?.length) return null;
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><Copy className="h-5 w-5 text-amber-500" />重复检测</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {duplicates.map((d) => (
          <div key={d.id} className="flex justify-between items-center p-3 rounded-lg border">
            <div><p className="font-medium">{d.name}</p><p className="text-sm text-muted-foreground">相似度: {d.similarity}%</p></div>
            <Button size="sm" variant="outline" onClick={() => onMerge([d.id])}>合并</Button>
          </div>
        ))}
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
          <div key={i} className="p-3 rounded-lg border"><p className="font-medium">{g.type}</p><p className="text-sm text-muted-foreground">{g.suggestion}</p></div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/hearing/hearing-outline.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Section { title: string; content: string; }
interface Props { sections: Section[]; }

export function HearingOutline({ sections }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>开庭提纲</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {sections.map((s, i) => (
          <div key={i}>
            <h4 className="font-medium">{s.title}</h4>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{s.content}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/hearing/hearing-template.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

const TEMPLATES = ['开庭陈述', '举证提纲', '质证意见', '发问提纲', '辩论意见', '最后陈述'];

interface Props { onSelect: (template: string) => void; }

export function HearingTemplate({ onSelect }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>庭审文书模板</CardTitle></CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {TEMPLATES.map((t) => <Button key={t} variant="outline" onClick={() => onSelect(t)}><FileText className="mr-2 h-4 w-4" />{t}</Button>)}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/hearing/trap-detector.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AlertTriangle } from 'lucide-react';
import { useState } from 'react';

interface Result { type: string; suggestion: string; }
interface Props { onDetect: (content: string) => void; result?: Result; }

export function TrapDetector({ onDetect, result }: Props) {
  const [content, setContent] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" />法庭陷阱识别</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="输入对方发言..." rows={3} />
        <Button onClick={() => onDetect(content)}>检测</Button>
        {result && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20">
            <p className="font-medium text-red-700 dark:text-red-400">{result.type}</p>
            <p className="text-sm mt-1">{result.suggestion}</p>
          </div>
        )}
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

writeFile('components/hearing/speaking-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { Gavel } from 'lucide-react';

interface Props { title: string; content: string; }

export function SpeakingCard({ title, content }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Gavel className="h-4 w-4 text-primary" />
          <p className="font-medium">{title}</p>
        </div>
        <p className="text-sm text-muted-foreground mt-2 whitespace-pre-wrap">{content}</p>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/hearing/cross-examination-panel.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface Opinion { authenticity: string; legality: string; relevance: string; opinion: string; }
interface Props { evidenceName: string; onSubmit: (opinion: Opinion) => void; }

export function CrossExaminationPanel({ evidenceName, onSubmit }: Props) {
  const [authenticity, setAuthenticity] = useState('认可');
  const [legality, setLegality] = useState('认可');
  const [relevance, setRelevance] = useState('认可');
  const [opinion, setOpinion] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>质证意见</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <p className="font-medium">{evidenceName}</p>
        <div className="grid grid-cols-3 gap-3">
          <div><label className="text-sm font-medium">真实性</label><select value={authenticity} onChange={(e) => setAuthenticity(e.target.value)} className="w-full rounded-md border p-2"><option>认可</option><option>异议</option></select></div>
          <div><label className="text-sm font-medium">合法性</label><select value={legality} onChange={(e) => setLegality(e.target.value)} className="w-full rounded-md border p-2"><option>认可</option><option>异议</option></select></div>
          <div><label className="text-sm font-medium">关联性</label><select value={relevance} onChange={(e) => setRelevance(e.target.value)} className="w-full rounded-md border p-2"><option>认可</option><option>异议</option></select></div>
        </div>
        <Textarea value={opinion} onChange={(e) => setOpinion(e.target.value)} placeholder="质证意见..." rows={3} />
        <Button onClick={() => onSubmit({ authenticity, legality, relevance, opinion })}>保存</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/hearing/hearing-record.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useHearingList } from '@/hooks/use-hearing';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function HearingRecord({ caseId }: Props) {
  const { data, isLoading } = useHearingList(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">出庭抗辩</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />添加开庭记录</Button></div>
      {!data?.length ? <p className="text-muted-foreground text-center py-8">暂无开庭记录</p> : (
        <div className="space-y-3">{data.map((h: any) => (<Card key={h.id}><CardContent className="p-4"><p className="font-medium">{h.courtName}</p><p className="text-sm text-muted-foreground">{h.date} · {h.type}</p></CardContent></Card>))}</div>
      )}
    </div>
  );
}
`);

writeFile('components/layout/breadcrumb.tsx', `import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Item { label: string; href?: string; }
interface Props { items: Item[]; }

export function Breadcrumb({ items }: Props) {
  return (
    <nav className="flex items-center text-sm text-muted-foreground">
      {items.map((item, i) => (
        <span key={i} className="flex items-center">
          {i > 0 && <ChevronRight className="h-4 w-4 mx-1" />}
          {item.href ? <Link to={item.href} className="hover:text-foreground">{item.label}</Link> : <span>{item.label}</span>}
        </span>
      ))}
    </nav>
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

writeFile('components/meeting/meeting-notes.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface Props { initialNotes?: string; onSave: (notes: string) => void; }

export function MeetingNotes({ initialNotes, onSave }: Props) {
  const [notes, setNotes] = useState(initialNotes || '');
  return (
    <Card>
      <CardHeader><CardTitle>会议纪要</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={10} placeholder="输入会议纪要..." />
        <Button onClick={() => onSave(notes)}>保存纪要</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/meeting/meeting-template.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const TYPES = ['商务谈判', '调解会议', '证据交换', '庭前会议'];

interface Props { onSelect: (type: string) => void; }

export function MeetingTemplate({ onSelect }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>会议类型</CardTitle></CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {TYPES.map((t) => <Button key={t} variant="outline" onClick={() => onSelect(t)}>{t}</Button>)}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/meeting/speech-to-text.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mic, Square } from 'lucide-react';

interface Props { onResult: (text: string) => void; }

export function SpeechToText({ onResult }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>语音转文字</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-center">
          <Button onClick={() => setIsRecording(!isRecording)} variant={isRecording ? 'destructive' : 'default'}>
            {isRecording ? <><Square className="mr-2 h-4 w-4" />停止</> : <><Mic className="mr-2 h-4 w-4" />开始录音</>}
          </Button>
        </div>
        {transcript && <div className="rounded border p-4 max-h-48 overflow-y-auto"><p className="text-sm whitespace-pre-wrap">{transcript}</p></div>}
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

writeFile('components/profile/interaction-history.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Interaction { action: string; timestamp: string; }
interface Props { interactions: Interaction[]; }

export function InteractionHistory({ interactions }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>交互历史</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {interactions.map((h, i) => (
          <div key={i} className="flex justify-between text-sm">
            <span>{h.action}</span>
            <span className="text-muted-foreground">{formatChineseDate(h.timestamp)}</span>
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

writeFile('components/profile/profile-summary.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCaseProfile } from '@/hooks/use-profile';
import { PageSkeleton } from '@/components/common/loading-skeleton';

interface Props { caseId: string; }

export function ProfileSummary({ caseId }: Props) {
  const { profile, isLoading } = useCaseProfile(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>案件画像</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {profile ? (
            <>
              <div><p className="text-sm text-muted-foreground">核心争议</p><p>{profile.coreDispute}</p></div>
              <div><p className="text-sm text-muted-foreground">胜诉概率</p><p>{profile.winProbability}%</p></div>
              <div><p className="text-sm text-muted-foreground">风险等级</p><p>{profile.riskLevel}</p></div>
            </>
          ) : <p className="text-muted-foreground">暂无画像数据</p>}
        </CardContent>
      </Card>
    </div>
  );
}
`);

writeFile('components/progress/milestone-generator.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useGenerateMilestones } from '@/hooks/use-deadline';

interface Props { caseId: string; }

export function MilestoneGenerator({ caseId }: Props) {
  const generate = useGenerateMilestones();
  return (
    <Card>
      <CardHeader><CardTitle>AI 生成里程碑</CardTitle></CardHeader>
      <CardContent><Button onClick={() => generate.mutate(caseId)} disabled={generate.isPending}>{generate.isPending ? '生成中...' : '生成里程碑'}</Button></CardContent>
    </Card>
  );
}
`);

writeFile('components/progress/stage-task-list.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Circle } from 'lucide-react';

interface Task { title: string; completed: boolean; }
interface Props { tasks: Task[]; }

export function StageTaskList({ tasks }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>阶段任务</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {tasks.map((t, i) => (
          <div key={i} className="flex items-center gap-3">
            {t.completed ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
            <span className={t.completed ? 'text-green-600' : ''}>{t.title}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/progress/workflow-config.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

const STAGES = ['收案', '签约', '证据', '调解', '诉讼', '保全', '开庭', '执行'];

interface Props { onSave: (stages: string[]) => void; }

export function WorkflowConfig({ onSave }: Props) {
  const [stages, setStages] = useState(STAGES);
  return (
    <Card>
      <CardHeader><CardTitle>流程配置</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">{stages.map((s, i) => <span key={s} className="px-3 py-1 rounded-full bg-primary/10 text-sm">{i + 1}. {s}</span>)}</div>
        <Button onClick={() => onSave(stages)}>保存配置</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/progress/stage-flow.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const STAGES = ['收案', '签约', '证据', '调解', '诉讼', '保全', '开庭', '执行'];

interface Props { caseId: string; }

export function StageFlow({ caseId }: Props) {
  const currentStage = 2;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>进度追踪</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            {STAGES.map((stage, i) => (
              <div key={stage} className="flex flex-col items-center">
                <div className={\`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium \${i < currentStage ? 'bg-green-500 text-white' : i === currentStage ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'}\`}>
                  {i < currentStage ? '✓' : i + 1}
                </div>
                <span className="mt-1 text-xs">{stage}</span>
                {i < STAGES.length - 1 && <div className={\`w-8 h-0.5 mt-4 \${i < currentStage ? 'bg-green-500' : 'bg-muted'}\`} />}
              </div>
            ))}
          </div>
          <p className="mt-6 text-center text-sm text-muted-foreground">当前阶段: {STAGES[currentStage]}</p>
        </CardContent>
      </Card>
    </div>
  );
}
`);

writeFile('components/report/report-generator.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useGenerateReport } from '@/hooks/use-report';
import { useState } from 'react';

const TYPES = [
  { value: 'case_analysis', label: '案件分析' },
  { value: 'litigation_strategy', label: '诉讼策略' },
  { value: 'full_analysis', label: '完整分析' },
  { value: 'evidence_report', label: '证据报告' },
  { value: 'milestone_report', label: '里程碑报告' },
  { value: 'opponent_analysis', label: '对手分析' },
];

interface Props { caseId: string; }

export function ReportGenerator({ caseId }: Props) {
  const [type, setType] = useState('case_analysis');
  const generate = useGenerateReport();
  return (
    <Card>
      <CardHeader><CardTitle>生成报告</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <select value={type} onChange={(e) => setType(e.target.value)} className="w-full rounded-md border p-2">
          {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <Button onClick={() => generate.mutate({ caseId, type })} disabled={generate.isPending}>{generate.isPending ? '生成中...' : '生成报告'}</Button>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/report/report-progress.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Props { progress: number; currentSection?: string; }

export function ReportProgress({ progress, currentSection }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>生成进度</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <Progress value={progress} />
        <p className="text-sm text-center">{progress}%</p>
        {currentSection && <p className="text-xs text-muted-foreground text-center">当前: {currentSection}</p>}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/report/report-viewer.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface Props { title: string; content: string; onExport: (format: string) => void; }

export function ReportViewer({ title, content, onExport }: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{title}</CardTitle>
          <Button size="sm" variant="outline" onClick={() => onExport('pdf')}><Download className="mr-2 h-4 w-4" />导出</Button>
        </div>
      </CardHeader>
      <CardContent><div className="prose max-w-none whitespace-pre-wrap">{content}</div></CardContent>
    </Card>
  );
}
`);

writeFile('components/report/report-list.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useReportList } from '@/hooks/use-report';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function ReportList({ caseId }: Props) {
  const { data, isLoading } = useReportList(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">报告中心</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />生成报告</Button></div>
      {!data?.length ? <p className="text-muted-foreground text-center py-8">暂无报告</p> : (
        <div className="space-y-3">{data.map((r: any) => (<Card key={r.id}><CardContent className="p-4"><p className="font-medium">{r.title}</p><p className="text-sm text-muted-foreground">{r.type} · {r.status}</p></CardContent></Card>))}</div>
      )}
    </div>
  );
}
`);

writeFile('components/senior-analysis/analysis-result.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { caseUnderstanding: string; strategySuggestions: string[]; riskWarnings: string[]; }

export function AnalysisResult({ caseUnderstanding, strategySuggestions, riskWarnings }: Props) {
  return (
    <div className="space-y-4">
      <Card><CardHeader><CardTitle>案件理解</CardTitle></CardHeader><CardContent><p className="text-sm whitespace-pre-wrap">{caseUnderstanding}</p></CardContent></Card>
      <Card><CardHeader><CardTitle>策略建议</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{strategySuggestions?.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle>风险提示</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{riskWarnings?.map((w, i) => <li key={i} className="text-sm text-red-600">{w}</li>)}</ul></CardContent></Card>
    </div>
  );
}
`);

writeFile('components/senior-analysis/analysis-selector.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useSeniorAnalysisHook } from '@/hooks/use-senior-analysis';

interface Props { caseId: string; }

export function AnalysisSelector({ caseId }: Props) {
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const { data, isLoading } = useSeniorAnalysisHook(caseId, depth);
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button variant={depth === 'quick' ? 'default' : 'outline'} onClick={() => setDepth('quick')}>快速</Button>
        <Button variant={depth === 'standard' ? 'default' : 'outline'} onClick={() => setDepth('standard')}>标准</Button>
        <Button variant={depth === 'deep' ? 'default' : 'outline'} onClick={() => setDepth('deep')}>深度</Button>
      </div>
      <Card>
        <CardHeader><CardTitle>资深律师分析 ({depth})</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? <p className="text-muted-foreground">分析中...</p> : data ? (
            <>
              <div><p className="text-sm text-muted-foreground">核心争议</p><p>{data.caseUnderstanding}</p></div>
              <div className="mt-3"><p className="text-sm text-muted-foreground">策略建议</p><ul className="list-disc pl-5">{data.strategySuggestions?.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul></div>
            </>
          ) : <p className="text-muted-foreground">暂无分析数据</p>}
        </CardContent>
      </Card>
    </div>
  );
}
`);

writeFile('components/senior-analysis/legal-requirements.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Requirement { name: string; status: string; risk: string; description?: string; }
interface Props { requirements: Requirement[]; }

export function LegalRequirements({ requirements }: Props) {
  const iconMap: Record<string, React.ReactNode> = {
    met: <CheckCircle className="h-4 w-4 text-green-500" />,
    partial: <AlertCircle className="h-4 w-4 text-amber-500" />,
    unmet: <XCircle className="h-4 w-4 text-red-500" />,
  };
  return (
    <Card>
      <CardHeader><CardTitle>法律要件分析</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {requirements?.map((r, i) => (
          <div key={i} className="flex items-start gap-3">
            {iconMap[r.status] || iconMap.unmet}
            <div>
              <p className="font-medium">{r.name}</p>
              {r.description && <p className="text-sm text-muted-foreground">{r.description}</p>}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/timeline/calendar-view.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { format, startOfMonth, endOfMonth, eachDayOfInterval } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface Props { deadlines: { date: string; title: string }[]; }

export function CalendarView({ deadlines }: Props) {
  const now = new Date();
  const days = eachDayOfInterval({ start: startOfMonth(now), end: endOfMonth(now) });
  return (
    <Card>
      <CardHeader><CardTitle>{format(now, 'yyyy 年 M 月', { locale: zhCN })}</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-1 text-center text-sm">
          <span className="font-medium">日</span><span className="font-medium">一</span><span className="font-medium">二</span><span className="font-medium">三</span><span className="font-medium">四</span><span className="font-medium">五</span><span className="font-medium">六</span>
          {days.map((d, i) => (
            <div key={i} className={\`p-2 rounded \${format(d, 'yyyy-MM-dd') === format(now, 'yyyy-MM-dd') ? 'bg-primary text-primary-foreground' : ''}\`}>
              <span>{format(d, 'd')}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/timeline/deadline-card.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { DeadlineCountdown } from '@/components/common/deadline-countdown';

interface Props { title: string; dueDate: string; daysRemaining: number; legalBasis?: string; }

export function DeadlineCard({ title, dueDate, daysRemaining, legalBasis }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-medium">{title}</p>
            {legalBasis && <p className="text-xs text-muted-foreground">{legalBasis}</p>}
          </div>
          <DeadlineCountdown dueDate={dueDate} daysRemaining={daysRemaining} />
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/timeline/deadline-chain.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Event { date: string; title: string; type: string; }
interface Props { events: Event[]; }

export function DeadlineChain({ events }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>期限链</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div><p className="text-sm font-medium">{e.title}</p><p className="text-xs text-muted-foreground">{formatChineseDate(e.date)} · {e.type}</p></div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/timeline/deadline-manager.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useDeadlineList } from '@/hooks/use-deadline';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';

interface Props { caseId: string; }

export function DeadlineManager({ caseId }: Props) {
  const { data, isLoading } = useDeadlineList(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">截止日期管理</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />添加截止日</Button></div>
      {!data?.length ? <p className="text-muted-foreground text-center py-8">暂无截止日期</p> : (
        <div className="space-y-3">{data.map((d: any) => (<Card key={d.id}><CardContent className="p-4"><div className="flex justify-between items-center"><div><p className="font-medium">{d.title}</p><p className="text-sm text-muted-foreground">{d.dueDate ? formatChineseDate(d.dueDate) : '未设置'}</p></div></div></CardContent></Card>))}</div>
      )}
    </div>
  );
}
`);

writeFile('components/timeline/deadline-reference.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const REFERENCES = [
  { name: '普通民事诉讼', period: '3年' },
  { name: '身体伤害', period: '1年' },
  { name: '租金纠纷', period: '1年' },
  { name: '借款纠纷', period: '3年' },
  { name: '答辩期', period: '15日' },
  { name: '举证期限', period: '30日' },
  { name: '民事上诉', period: '15日' },
  { name: '执行申请', period: '2年' },
];

export function DeadlineReference() {
  return (
    <Card>
      <CardHeader><CardTitle>常用法定期限参考</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {REFERENCES.map((r) => (
            <div key={r.name} className="flex justify-between text-sm">
              <span>{r.name}</span>
              <span className="font-medium">{r.period}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/timeline/letter-manager.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useLetterList } from '@/hooks/use-letter';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus } from 'lucide-react';

interface Props { caseId: string; }

export function LetterManager({ caseId }: Props) {
  const { data, isLoading } = useLetterList(caseId);
  if (isLoading) return <PageSkeleton />;
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">函件管理</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />新建函件</Button></div>
      {!data?.length ? <p className="text-muted-foreground text-center py-8">暂无函件</p> : (
        <div className="space-y-3">{data.map((l: any) => (<Card key={l.id}><CardContent className="p-4"><p className="font-medium">{l.title}</p><p className="text-sm text-muted-foreground">{l.category} · {l.mailStatus}</p></CardContent></Card>))}</div>
      )}
    </div>
  );
}
`);

writeFile('components/timeline/urgency-report.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle } from 'lucide-react';
import { formatChineseDate } from '@/lib/date';

interface Deadline { title: string; dueDate: string; daysRemaining: number; }
interface Props { deadlines: Deadline[]; }

export function UrgencyReport({ deadlines }: Props) {
  const urgent = deadlines.filter((d) => d.daysRemaining <= 7).sort((a, b) => a.daysRemaining - b.daysRemaining);
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" />紧迫度报告</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {urgent.map((d, i) => (
          <div key={i} className="flex justify-between items-center">
            <div><p className="font-medium">{d.title}</p><p className="text-xs text-muted-foreground">{formatChineseDate(d.dueDate)}</p></div>
            <span className="text-sm font-medium text-red-600">{d.daysRemaining} 天</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/execution/execution-dashboard.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useExecutionData } from '@/hooks/use-execution';
import { PageSkeleton } from '@/components/common/loading-skeleton';

interface Props { caseId: string; }

export function ExecutionDashboard({ caseId }: Props) {
  const { data, isLoading } = useExecutionData(caseId);
  if (isLoading) return <PageSkeleton />;
  if (!data) return <p className="text-muted-foreground text-center py-8">暂无执行数据</p>;
  const progress = data.totalAmount ? Math.round((data.executedAmount / data.totalAmount) * 100) : 0;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>执行跟踪</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div><p className="text-sm text-muted-foreground">执行总额</p><p className="text-xl font-bold">¥{data.totalAmount?.toLocaleString()}</p></div>
            <div><p className="text-sm text-muted-foreground">已执行</p><p className="text-xl font-bold text-green-600">¥{data.executedAmount?.toLocaleString()}</p></div>
            <div><p className="text-sm text-muted-foreground">剩余</p><p className="text-xl font-bold text-red-600">¥{data.remainingAmount?.toLocaleString()}</p></div>
          </div>
          <Progress value={progress} />
          <p className="text-sm text-muted-foreground text-center">{progress}% 已完成</p>
        </CardContent>
      </Card>
    </div>
  );
}
`);

writeFile('components/execution/execution-progress.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Props { totalAmount: number; executedAmount: number; }

export function ExecutionProgress({ totalAmount, executedAmount }: Props) {
  const progress = totalAmount ? Math.round((executedAmount / totalAmount) * 100) : 0;
  return (
    <Card>
      <CardHeader><CardTitle>执行进度</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Progress value={progress} />
        <div className="grid grid-cols-3 gap-4 text-center">
          <div><p className="text-sm text-muted-foreground">执行总额</p><p className="text-lg font-bold">¥{totalAmount?.toLocaleString()}</p></div>
          <div><p className="text-sm text-muted-foreground">已执行</p><p className="text-lg font-bold text-green-600">¥{executedAmount?.toLocaleString()}</p></div>
          <div><p className="text-sm text-muted-foreground">剩余</p><p className="text-lg font-bold text-red-600">¥{(totalAmount - executedAmount)?.toLocaleString()}</p></div>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/execution/execution-record.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatChineseDate } from '@/lib/date';

interface Record { date: string; type: string; amount?: number; description: string; operator?: string; }
interface Props { records: Record[]; }

export function ExecutionRecordList({ records }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>执行记录</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {!records?.length ? <p className="text-muted-foreground text-center py-4">暂无记录</p> : records.map((r, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-primary mt-2" />
            <div>
              <p className="text-sm font-medium">{r.type}</p>
              <p className="text-xs text-muted-foreground">{formatChineseDate(r.date)}{r.amount != null ? ' · ¥' + r.amount.toLocaleString() : ''}</p>
              {r.description && <p className="text-xs text-muted-foreground">{r.description}</p>}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/execution/execution-tools.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Shield, Ban, AlertTriangle, Handshake } from 'lucide-react';

const TOOLS = [
  { icon: FileText, label: '申请执行', action: 'apply' },
  { icon: Shield, label: '财产保全', action: 'preserve' },
  { icon: Ban, label: '限制高消费', action: 'restrict' },
  { icon: AlertTriangle, label: '纳入失信', action: 'blacklist' },
  { icon: Handshake, label: '执行和解', action: 'settle' },
];

interface Props { onAction: (action: string) => void; }

export function ExecutionTools({ onAction }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>执行辅助工具</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {TOOLS.map((t) => (
            <Button key={t.action} variant="outline" className="flex items-center justify-center gap-2" onClick={() => onAction(t.action)}>
              <t.icon className="h-4 w-4" />{t.label}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/appeal/appeal-overview.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
      <div className="flex justify-between items-center"><h2 className="text-lg font-bold">上诉追踪</h2><Button size="sm"><Plus className="mr-2 h-4 w-4" />新建上诉</Button></div>
      {!data?.length ? <p className="text-muted-foreground text-center py-8">暂无上诉记录</p> : (
        <div className="space-y-3">{data.map((a: any) => (<Card key={a.id}><CardContent className="p-4"><p className="font-medium">{a.originalCourt}</p><p className="text-sm text-muted-foreground">上诉期限: {a.appealDeadline} · 状态: {a.status}</p></CardContent></Card>))}</div>
      )}
    </div>
  );
}
`);

writeFile('components/party/party-list.tsx', `import { Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Party } from '@/types/party.types';

interface Props { parties: Party[]; isLoading: boolean; onAdd: () => void; onSelect: (party: Party) => void; }

export function PartyList({ parties, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-16 rounded bg-muted" /><div className="h-16 rounded bg-muted" /></div>;
  if (parties.length === 0) return (
    <div className="text-center py-8">
      <Users className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-2 text-muted-foreground">暂无当事人</p>
      <Button onClick={onAdd} className="mt-4">添加当事人</Button>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center"><h3 className="font-semibold">当事人 ({parties.length})</h3><Button size="sm" onClick={onAdd}>添加</Button></div>
      {parties.map((p) => (
        <Card key={p.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(p)}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="font-medium">{p.name}</p><p className="text-sm text-muted-foreground">{p.role} · {p.phone || '无电话'}</p></div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
`);

writeFile('components/party/party-detail.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Party } from '@/types/party.types';
import { CompanyInfo } from '@/components/common/company-info';

interface Props { party: Party; onEdit: () => void; onDelete: () => void; }

export function PartyDetail({ party, onEdit, onDelete }: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{party.name}</CardTitle>
          <div className="flex gap-2">
            <button onClick={onEdit} className="text-sm text-primary hover:underline">编辑</button>
            <button onClick={onDelete} className="text-sm text-red-500 hover:underline">删除</button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div><p className="text-sm text-muted-foreground">角色</p><p>{party.role}</p></div>
        {party.phone && <div><p className="text-sm text-muted-foreground">电话</p><p>{party.phone}</p></div>}
        {party.email && <div><p className="text-sm text-muted-foreground">邮箱</p><p>{party.email}</p></div>}
        {party.address && <div><p className="text-sm text-muted-foreground">地址</p><p>{party.address}</p></div>}
        {party.agent && <div><p className="text-sm text-muted-foreground">代理人</p><p>{party.agent} {party.agentPhone ? '(' + party.agentPhone + ')' : ''}</p></div>}
        {party.companyInfo && <CompanyInfo name={party.companyInfo.name} creditCode={party.companyInfo.creditCode} legalRepresentative={party.companyInfo.legalRepresentative} status={party.companyInfo.status} />}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/party/party-relation.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Party { id: string; name: string; role: string; }
interface Relation { from: string; to: string; label: string; }
interface Props { parties: Party[]; relations: Relation[]; }

export function PartyRelation({ parties, relations }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>当事人关系图</CardTitle></CardHeader>
      <CardContent>
        <div className="h-[400px] flex items-center justify-center rounded-lg border bg-muted/20">
          <p className="text-muted-foreground">当事人关系可视化区域</p>
        </div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/party/party-role-badge.tsx', `import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const partyRoleVariants = cva('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', {
  variants: {
    role: {
      plaintiff: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      defendant: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      third_party: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      counter_claimant: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      counter_defendant: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    },
  },
  defaultVariants: { role: 'plaintiff' },
});

interface Props extends VariantProps<typeof partyRoleVariants> { label: string; }

export function PartyRoleBadge({ label, role }: Props) {
  return <span className={cn(partyRoleVariants({ role }))}>{label}</span>;
}
`);

writeFile('components/thread/thread-list.tsx', `import { ListTodo } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CaseThread } from '@/types/thread.types';

interface Props { threads: CaseThread[]; isLoading: boolean; onAdd: () => void; onSelect: (thread: CaseThread) => void; }

export function ThreadList({ threads, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-16 rounded bg-muted" /></div>;
  if (threads.length === 0) return (
    <div className="text-center py-8">
      <ListTodo className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-2 text-muted-foreground">暂无线索</p>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center"><h3 className="font-semibold">线索 ({threads.length})</h3><button onClick={onAdd} className="text-sm text-primary hover:underline">添加</button></div>
      {threads.map((t) => (
        <Card key={t.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(t)}>
          <CardContent className="p-4"><p className="font-medium">{t.title}</p><p className="text-sm text-muted-foreground">{t.status} · {t.priority}</p></CardContent>
        </Card>
      ))}
    </div>
  );
}
`);

writeFile('components/thread/thread-form.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

interface Props { onSubmit: (data: { title: string; description: string; priority: string }) => void; onCancel: () => void; }

export function ThreadForm({ onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  return (
    <Card>
      <CardHeader><CardTitle>新增线索</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><label className="text-sm font-medium">标题</label><Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="线索标题" /></div>
        <div><label className="text-sm font-medium">描述</label><Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="线索描述" /></div>
        <div><label className="text-sm font-medium">优先级</label><select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full rounded-md border p-2"><option value="high">高</option><option value="medium">中</option><option value="low">低</option></select></div>
        <div className="flex justify-end gap-2"><Button variant="outline" onClick={onCancel}>取消</Button><Button onClick={() => onSubmit({ title, description, priority })}>保存</Button></div>
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/thread/counter-claim-list.tsx', `import { Scale } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CounterClaim } from '@/types/thread.types';

interface Props { claims: CounterClaim[]; isLoading: boolean; onAdd: () => void; onSelect: (claim: CounterClaim) => void; }

export function CounterClaimList({ claims, isLoading, onAdd, onSelect }: Props) {
  if (isLoading) return <div className="animate-pulse space-y-3"><div className="h-16 rounded bg-muted" /></div>;
  if (claims.length === 0) return (
    <div className="text-center py-8">
      <Scale className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-2 text-muted-foreground">暂无反诉</p>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center"><h3 className="font-semibold">反诉/追加请求 ({claims.length})</h3><button onClick={onAdd} className="text-sm text-primary hover:underline">添加</button></div>
      {claims.map((c) => (
        <Card key={c.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(c)}>
          <CardContent className="p-4"><p className="font-medium">{c.title}</p><p className="text-sm text-muted-foreground">{c.status} {c.amount ? '· ¥' + c.amount.toLocaleString() : ''}</p></CardContent>
        </Card>
      ))}
    </div>
  );
}
`);

writeFile('components/thread/counter-claim-form.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

interface Props { onSubmit: (data: { title: string; description: string; amount?: number }) => void; onCancel: () => void; }

export function CounterClaimForm({ onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>新增反诉/追加请求</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><label className="text-sm font-medium">标题</label><Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="反诉标题" /></div>
        <div><label className="text-sm font-medium">描述</label><Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="反诉描述" /></div>
        <div><label className="text-sm font-medium">金额 (可选)</label><Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="反诉金额" /></div>
        <div className="flex justify-end gap-2"><Button variant="outline" onClick={onCancel}>取消</Button><Button onClick={() => onSubmit({ title, description, amount: amount ? Number(amount) : undefined })}>保存</Button></div>
      </CardContent>
    </Card>
  );
}
`);

// Fix remaining broken files
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

writeFile('components/adversarial/issue-card.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Issue } from '@/types/issue.types';

interface Props { issue: Issue; onClick: () => void; }

export function IssueCard({ issue, onClick }: Props) {
  const priorityColors: Record<string, string> = { high: 'destructive', medium: 'default', low: 'secondary' };
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-base">{issue.title}</CardTitle>
          <Badge variant={(priorityColors[issue.priority] || 'secondary') as 'default'}>{issue.priority}</Badge>
        </div>
      </CardHeader>
      <CardContent><p className="text-sm text-muted-foreground line-clamp-2">{issue.ourPosition}</p></CardContent>
    </Card>
  );
}
`);

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

writeFile('components/adversarial/evidence-matrix-table.tsx', `import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface Props { evidence: any[]; issues: any[]; }

export function EvidenceMatrixTable({ evidence, issues }: Props) {
  return (
    <Table>
      <TableHeader><TableRow><TableHead>证据</TableHead>{issues.map((i) => <TableHead key={i.id}>{i.title}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{evidence.map((e) => <TableRow key={e.id}><TableCell>{e.name}</TableCell>{issues.map((i) => <TableCell key={i.id}>-</TableCell>)}</TableRow>)}</TableBody>
    </Table>
  );
}
`);

writeFile('components/adversarial/scenario-prediction.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface Scenario { scenario: string; probability: number; description: string; }
interface Props { scenarios: Scenario[]; }

export function ScenarioPrediction({ scenarios }: Props) {
  if (!scenarios?.length) return <p className="text-muted-foreground text-center py-8">暂无预测数据</p>;
  return (
    <Card>
      <CardHeader><CardTitle>情景预测</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {scenarios.map((s, i) => (
          <div key={i}>
            <div className="flex justify-between text-sm mb-1"><span>{s.scenario}</span><span>{s.probability}%</span></div>
            <Progress value={s.probability} />
            <p className="text-xs text-muted-foreground mt-1">{s.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

writeFile('components/adversarial/swot-quadrant.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { strengths: string[]; weaknesses: string[]; opponentWeaknesses: string[]; opponentStrengths: string[]; }

export function SwotQuadrant({ strengths, weaknesses, opponentWeaknesses, opponentStrengths }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card><CardHeader><CardTitle className="text-green-600">我方优势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{strengths.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-red-600">我方劣势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{weaknesses.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-amber-600">对方劣势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{opponentWeaknesses.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-blue-600">对方优势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{opponentStrengths.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
    </div>
  );
}
`);

writeFile('components/adversarial/action-plan.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Circle } from 'lucide-react';

interface Props { actions: string[]; onAction: (action: string) => void; }

export function ActionPlan({ actions, onAction }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>行动计划</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {actions.map((a, i) => (
          <div key={i} className="flex items-center gap-3">
            <Circle className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm flex-1">{a}</span>
            <Button size="sm" variant="outline" onClick={() => onAction(a)}>执行</Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
`);

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

writeFile('components/appeal/appeal-argument.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

console.log('All components fixed!');
