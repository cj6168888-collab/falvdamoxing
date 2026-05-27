import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Props { onSubmit: (data: Record<string, string>) => void; onCancel: () => void; }

export function PartyForm({ onSubmit, onCancel }: Props) {
  const [name, setName] = useState('');
  const [role, setRole] = useState('plaintiff');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>添加当事人</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><Label>姓名</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
        <div><Label>角色</Label>
          <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full rounded-md border p-2">
            <option value="plaintiff">原告</option>
            <option value="defendant">被告</option>
            <option value="third_party">第三人</option>
          </select>
        </div>
        <div><Label>电话</Label><Input value={phone} onChange={(e) => setPhone(e.target.value)} /></div>
        <div><Label>地址</Label><Input value={address} onChange={(e) => setAddress(e.target.value)} /></div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>取消</Button>
          <Button onClick={() => onSubmit({ name, role, phone, address })}>保存</Button>
        </div>
      </CardContent>
    </Card>
  );
}
