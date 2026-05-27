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

// Fix hearing-record.tsx
writeFile('components/hearing/hearing-record.tsx', `import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">出庭抗辩</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />添加开庭记录</Button>
      </div>
      {!data?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无开庭记录</p>
      ) : (
        <div className="space-y-3">
          {data.map((h: any) => (
            <Card key={h.id}><CardContent className="p-4"><p className="font-medium">{h.courtName}</p><p className="text-sm text-muted-foreground">{h.date} · {h.type}</p></CardContent></Card>
          ))}
        </div>
      )}
    </div>
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

// Fix party-list.tsx
writeFile('components/party/party-list.tsx', `import { Users } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">当事人 ({parties.length})</h3>
        <Button size="sm" onClick={onAdd}>添加</Button>
      </div>
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

// Fix report-list.tsx
writeFile('components/report/report-list.tsx', `import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">报告中心</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />生成报告</Button>
      </div>
      {!data?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无报告</p>
      ) : (
        <div className="space-y-3">
          {data.map((r: any) => (
            <Card key={r.id}><CardContent className="p-4"><p className="font-medium">{r.title}</p><p className="text-sm text-muted-foreground">{r.type} · {r.status}</p></CardContent></Card>
          ))}
        </div>
      )}
    </div>
  );
}
`);

// Fix counter-claim-list.tsx
writeFile('components/thread/counter-claim-list.tsx', `import { Scale } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">反诉/追加请求 ({claims.length})</h3>
        <button onClick={onAdd} className="text-sm text-primary hover:underline">添加</button>
      </div>
      {claims.map((c) => (
        <Card key={c.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(c)}>
          <CardContent className="p-4"><p className="font-medium">{c.title}</p><p className="text-sm text-muted-foreground">{c.status} {c.amount ? '· ¥' + c.amount.toLocaleString() : ''}</p></CardContent>
        </Card>
      ))}
    </div>
  );
}
`);

// Fix thread-list.tsx
writeFile('components/thread/thread-list.tsx', `import { ListTodo } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">线索 ({threads.length})</h3>
        <button onClick={onAdd} className="text-sm text-primary hover:underline">添加</button>
      </div>
      {threads.map((t) => (
        <Card key={t.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(t)}>
          <CardContent className="p-4"><p className="font-medium">{t.title}</p><p className="text-sm text-muted-foreground">{t.status} · {t.priority}</p></CardContent>
        </Card>
      ))}
    </div>
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

// Fix deadline-manager.tsx
writeFile('components/timeline/deadline-manager.tsx', `import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">截止日期管理</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />添加截止日</Button>
      </div>
      {!data?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无截止日期</p>
      ) : (
        <div className="space-y-3">
          {data.map((d: any) => (
            <Card key={d.id}><CardContent className="p-4"><div className="flex justify-between items-center"><div><p className="font-medium">{d.title}</p><p className="text-sm text-muted-foreground">{d.dueDate ? formatChineseDate(d.dueDate) : '未设置'}</p></div></div></CardContent></Card>
          ))}
        </div>
      )}
    </div>
  );
}
`);

// Fix letter-manager.tsx
writeFile('components/timeline/letter-manager.tsx', `import { Card, CardContent } from '@/components/ui/card';
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
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">函件管理</h2>
        <Button size="sm"><Plus className="mr-2 h-4 w-4" />新建函件</Button>
      </div>
      {!data?.length ? (
        <p className="text-muted-foreground text-center py-8">暂无函件</p>
      ) : (
        <div className="space-y-3">
          {data.map((l: any) => (
            <Card key={l.id}><CardContent className="p-4"><p className="font-medium">{l.title}</p><p className="text-sm text-muted-foreground">{l.category} · {l.mailStatus}</p></CardContent></Card>
          ))}
        </div>
      )}
    </div>
  );
}
`);

console.log('All remaining components fixed!');
