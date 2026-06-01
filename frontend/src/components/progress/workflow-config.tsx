import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

const STAGES = ['接案评估', '委托确认', '证据整理', '诉前沟通', '立案/应诉', '保全', '开庭准备', '执行跟踪'];

interface Props { onSave: (stages: string[]) => void; }

export function WorkflowConfig({ onSave }: Props) {
  const [stages] = useState(STAGES);
  return (
    <Card>
      <CardHeader><CardTitle>办案流程配置</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">{stages.map((s, i) => <span key={s} className="px-3 py-1 rounded-full bg-primary/10 text-sm">{i + 1}. {s}</span>)}</div>
        <Button onClick={() => onSave(stages)}>保存配置</Button>
      </CardContent>
    </Card>
  );
}
