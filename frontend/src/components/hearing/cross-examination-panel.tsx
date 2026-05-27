import { useState } from 'react';
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
