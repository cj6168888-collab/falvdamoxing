import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

interface Props { onSubmit: (data: { title: string; description: string; amount?: number }) => void; onCancel: () => void; }

export function CounterClaimForm({ onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>新增反诉/追加请求</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><label className="text-sm font-medium">标题</label><Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="反诉标题" /></div>
        <div><label className="text-sm font-medium">描述</label><Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="反诉描述" /></div>
        <div><label className="text-sm font-medium">金额 (可选)</label><Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="反诉金额" /></div>
        <div className="flex justify-end gap-2"><Button variant="outline" onClick={onCancel}>取消</Button><Button onClick={() => onSubmit({ title, description, amount: amount ? Number(amount) : undefined })}>保存</Button></div>
      </CardContent>
    </Card>
  );
}
