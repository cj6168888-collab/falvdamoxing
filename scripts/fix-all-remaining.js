const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
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
        <CardHeader>
          <CardTitle>四象限分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border p-4">
              <h4 className="font-medium text-green-600">我方优势</h4>
              <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
            </div>
            <div className="rounded-lg border p-4">
              <h4 className="font-medium text-red-600">我方劣势</h4>
              <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
            </div>
            <div className="rounded-lg border p-4">
              <h4 className="font-medium text-amber-600">对方劣势</h4>
              <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
            </div>
            <div className="rounded-lg border p-4">
              <h4 className="font-medium text-blue-600">对方优势</h4>
              <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
            </div>
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
      <CardHeader>
        <CardTitle>导入到庭审</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">将对抗性分析结果导入到出庭抗辩模块</p>
        <Button onClick={onImport}>
          <FileText className="mr-2 h-4 w-4" />导入
        </Button>
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

// Fix appeal-doc-generator.tsx
writeFile('components/appeal/appeal-doc-generator.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

interface Props { caseId: string; onGenerate: (type: string) => void; }

export function AppealDocGenerator({ caseId, onGenerate }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>上诉文书生成</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full" onClick={() => onGenerate('上诉状')}>
          <FileText className="mr-2 h-4 w-4" />生成上诉状
        </Button>
        <Button className="w-full" variant="outline" onClick={() => onGenerate('答辩意见')}>
          <FileText className="mr-2 h-4 w-4" />生成答辩意见
        </Button>
        <Button className="w-full" variant="outline" onClick={() => onGenerate('新证据清单')}>
          <FileText className="mr-2 h-4 w-4" />生成新证据清单
        </Button>
      </CardContent>
    </Card>
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
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4" />
            {title}
          </CardTitle>
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
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <span>{title}</span>
          </div>
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

// Fix evidence-analysis-chat.tsx
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
        <div className="h-64 overflow-y-auto rounded border p-4">
          <p className="text-sm text-muted-foreground">询问关于此证据的问题...</p>
        </div>
        <div className="flex gap-2">
          <Textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入问题..." className="flex-1" />
          <Button>发送</Button>
        </div>
      </CardContent>
    </Card>
  );
}
`);

// Fix evidence-annotation.tsx
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

// Fix evidence-graph.tsx
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

// Fix real-time-analysis.tsx
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

// Fix panel-layout.tsx
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

// Fix audio-player.tsx
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

// Fix meeting-recorder.tsx
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

// Fix speech-to-text.tsx
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

// Fix party-relation.tsx
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

// Fix knowledge-graph.tsx
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

// Fix stage-flow.tsx
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

// Fix workflow-config.tsx
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

// Fix calendar-view.tsx
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

console.log('All remaining components fixed!');
