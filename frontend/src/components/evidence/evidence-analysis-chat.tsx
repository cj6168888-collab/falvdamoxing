import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface Props { evidenceId: string; }

export function EvidenceAnalysisChat({ evidenceId: _evidenceId }: Props) {
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
