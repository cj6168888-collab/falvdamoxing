import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

interface Props { onSubmit: (data: { title: string; description: string; priority: string }) => void; onCancel: () => void; }

export function ThreadForm({ onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  return (
    <Card>
      <CardHeader><CardTitle>新增线索</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><label className="text-sm font-medium">标题</label><Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="线索标题" /></div>
        <div><label className="text-sm font-medium">描述</label><Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="线索描述" /></div>
        <div><label className="text-sm font-medium">优先级</label><select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full rounded-md border p-2"><option value="high">高</option><option value="medium">中</option><option value="low">低</option></select></div>
        <div className="flex justify-end gap-2"><Button variant="outline" onClick={onCancel}>取消</Button><Button onClick={() => onSubmit({ title, description, priority })}>保存</Button></div>
      </CardContent>
    </Card>
  );
}
