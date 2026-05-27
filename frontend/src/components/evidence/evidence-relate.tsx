import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Link } from 'lucide-react';
import { useState } from 'react';

interface Props {
  evidenceId: string;
  onRelate: (targetId: string) => void;
}

export function EvidenceRelate({ evidenceId, onRelate }: Props) {
  const [targetId, setTargetId] = useState('');

  return (
    <Card>
      <CardHeader>
        <CardTitle>关联管理</CardTitle>
        <p className="text-xs text-muted-foreground">当前证据：{evidenceId}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <Link className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">关联到文书、争点或其他证据</span>
        </div>
        <div>
          <Label htmlFor="evidence-relate-target">关联对象 ID</Label>
          <Input
            id="evidence-relate-target"
            value={targetId}
            onChange={(event) => setTargetId(event.target.value)}
            placeholder="输入要关联的对象 ID"
          />
        </div>
        <Button size="sm" disabled={!targetId.trim()} onClick={() => onRelate(targetId.trim())}>
          添加关联
        </Button>
      </CardContent>
    </Card>
  );
}
