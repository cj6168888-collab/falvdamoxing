import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';

interface Props {
  evidenceId: string;
  onSubmit: (corrections: Record<string, string>) => void;
}

export function CorrectionForm({ evidenceId, onSubmit }: Props) {
  const [type, setType] = useState('');
  const [proofDirection, setProofDirection] = useState('');

  return (
    <Card>
      <CardHeader>
        <CardTitle>人工纠偏</CardTitle>
        <p className="text-xs text-muted-foreground">证据编号：{evidenceId}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="evidence-type-correction">证据类型</Label>
          <Input
            id="evidence-type-correction"
            value={type}
            onChange={(event) => setType(event.target.value)}
            placeholder="修正类型"
          />
        </div>
        <div>
          <Label htmlFor="proof-direction-correction">证明方向</Label>
          <Input
            id="proof-direction-correction"
            value={proofDirection}
            onChange={(event) => setProofDirection(event.target.value)}
            placeholder="修正证明方向"
          />
        </div>
        <Button onClick={() => onSubmit({ type, proofDirection })}>提交纠偏</Button>
      </CardContent>
    </Card>
  );
}
