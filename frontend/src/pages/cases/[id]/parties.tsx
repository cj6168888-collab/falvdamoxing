import { PartyList } from '@/components/party/party-list';
import { PartyDetail } from '@/components/party/party-detail';
import { usePartyList, useCreateParty, useUpdateParty, useDeleteParty } from '@/hooks/use-party';
import { useParams } from 'react-router-dom';
import { useState } from 'react';
import type { Party } from '@/types/party.types';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

export default function CasePartiesPage() {
  const { id } = useParams<{ id: string }>();
  const { data: parties, isLoading, refetch } = usePartyList(id || '');
  const [selectedParty, setSelectedParty] = useState<Party | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingParty, setEditingParty] = useState<Party | null>(null);
  const [formData, setFormData] = useState({ name: '', role: 'plaintiff', phone: '', email: '', address: '' });

  const createParty = useCreateParty();
  const updateParty = useUpdateParty();
  const deleteParty = useDeleteParty();

  const handleAdd = () => {
    setEditingParty(null);
    setFormData({ name: '', role: 'plaintiff', phone: '', email: '', address: '' });
    setShowDialog(true);
  };

  const handleEdit = (party: Party) => {
    setEditingParty(party);
    setFormData({ name: party.name, role: party.role, phone: party.phone || '', email: party.email || '', address: party.address || '' });
    setShowDialog(true);
  };

  const handleDelete = async (party: Party) => {
    if (!confirm(`确定删除当事人「${party.name}」？`)) return;
    try {
      await deleteParty.mutateAsync({ caseId: id!, partyId: String(party.id) });
      toast.success('当事人已删除');
      setSelectedParty(null);
      refetch();
    } catch {
      toast.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) { toast.error('请输入姓名'); return; }
    try {
      if (editingParty) {
        await updateParty.mutateAsync({ caseId: id!, partyId: String(editingParty.id), data: formData });
        toast.success('当事人已更新');
      } else {
        await createParty.mutateAsync({ caseId: id!, data: formData });
        toast.success('当事人已添加');
      }
      setShowDialog(false);
      refetch();
    } catch {
      toast.error(editingParty ? '更新失败' : '添加失败');
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <PartyList parties={parties || []} isLoading={isLoading} onAdd={handleAdd} onSelect={setSelectedParty} />
      </div>
      <div>
        {selectedParty ? (
          <PartyDetail party={selectedParty} onEdit={() => handleEdit(selectedParty)} onDelete={() => handleDelete(selectedParty)} />
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <p>选择当事人查看详情</p>
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingParty ? '编辑当事人' : '添加当事人'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div><Label>姓名 *</Label><Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="请输入姓名" /></div>
            <div>
              <Label>角色</Label>
              <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="plaintiff">原告</SelectItem>
                  <SelectItem value="defendant">被告</SelectItem>
                  <SelectItem value="third_party">第三人</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>电话</Label><Input value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} placeholder="联系电话" /></div>
            <div><Label>邮箱</Label><Input value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="电子邮箱" /></div>
            <div><Label>地址</Label><Input value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} placeholder="联系地址" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>取消</Button>
            <Button onClick={handleSubmit} disabled={createParty.isPending || updateParty.isPending}>{editingParty ? '保存' : '添加'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
