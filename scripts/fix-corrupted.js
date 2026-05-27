const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
  fs.writeFileSync(fullPath, content, 'utf-8');
  console.log('Fixed:', relPath);
}

// Fix letter-card.tsx (corrupted by PowerShell)
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

console.log('All corrupted files fixed!');
