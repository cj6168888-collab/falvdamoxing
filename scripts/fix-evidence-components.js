const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
  fs.writeFileSync(fullPath, content, 'utf-8');
  console.log('Fixed:', relPath);
}

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
        <div className="flex gap-2">
          <Textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入问题..." className="flex-1" />
          <Button>发送</Button>
        </div>
      </CardContent>
    </Card>
  );
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

console.log('All evidence components fixed!');
