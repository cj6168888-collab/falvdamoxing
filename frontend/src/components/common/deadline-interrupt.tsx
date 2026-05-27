import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useState } from 'react';

interface Props { onSubmit: (data: { type: string; date: string; description: string }) => void; }

export function DeadlineInterrupt({ onSubmit }: Props) {
  const [type, setType] = useState('');
  const [date, setDate] = useState('');
  const [description, setDescription] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>中断/顺延事件</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <select value={type} onChange={(e) => setType(e.target.value)} className="w-full rounded-md border p-2">
          <option value="">选择事件类型</option>
          <option value="催款函">催款函</option>
          <option value="起诉">起诉</option>
          <option value="和解协议">和解协议</option>
          <option value="调解">调解</option>
        </select>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="事件描述" />
        <Button onClick={() => onSubmit({ type, date, description })} disabled={!type || !date}>保存</Button>
      </CardContent>
    </Card>
  );
}
