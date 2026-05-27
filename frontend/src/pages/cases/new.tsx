import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CaseTemplateCard } from '@/components/common/case-template-card';
import { useCreateCase } from '@/hooks/use-case';
import type { Case } from '@/types/case.types';

const TEMPLATES = [
  { type: 'loan', label: '借贷纠纷', fields: ['当事人', '金额'], evidence: ['借条', '转账记录'], documents: ['律师函', '起诉状'] },
  { type: 'contract', label: '合同纠纷', fields: ['当事人', '合同类型'], evidence: ['合同原件', '变更协议'], documents: ['解除通知', '起诉状'] },
  { type: 'tort', label: '侵权纠纷', fields: ['当事人', '侵权行为'], evidence: ['现场照片', '医疗记录'], documents: ['起诉状', '鉴定申请'] },
  { type: 'labor', label: '劳动争议', fields: ['员工/企业', '诉求类型'], evidence: ['劳动合同', '工资流水'], documents: ['仲裁申请'] },
];

export default function CaseNewPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [plaintiffName, setPlaintiffName] = useState('');
  const [defendantName, setDefendantName] = useState('');
  const [amount, setAmount] = useState('');
  const createCase = useCreateCase();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        title,
        case_type: type,
        description,
        plaintiff: plaintiffName,
        defendant: defendantName,
        claim_amount: amount || undefined,
      } as unknown as Partial<Case>;
      const result = await createCase.mutateAsync(payload);
      navigate(`/cases/${result.id}`);
    } catch (err) { console.error(err); }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      <div className="mb-6 flex items-center justify-between"><h1 className="text-2xl font-bold">新建案件</h1><Button variant="outline" onClick={() => navigate(-1)}>返回</Button></div>
      <div className="mb-8">
        <h2 className="mb-4 text-lg font-semibold">选择案件模板</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {TEMPLATES.map((t) => <CaseTemplateCard key={t.type} {...t} onSelect={() => setType(t.type)} />)}
        </div>
      </div>
      <Card>
        <CardHeader><CardTitle>案件信息 {type && `(已选择: ${TEMPLATES.find(t=>t.type===type)?.label})`}</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label>案件标题 *</Label><Input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="请输入案件标题" /></div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div><Label>原告姓名 *</Label><Input value={plaintiffName} onChange={(e) => setPlaintiffName(e.target.value)} required placeholder="原告姓名" /></div>
              <div><Label>被告姓名 *</Label><Input value={defendantName} onChange={(e) => setDefendantName(e.target.value)} required placeholder="被告姓名" /></div>
            </div>
            <div><Label>诉讼金额</Label><Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="请输入金额" /></div>
            <div><Label>案件描述</Label><Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="请描述案件情况" /></div>

            {/* 证据管理提示 */}
            <div className="rounded-lg border bg-muted/50 p-4">
              <h3 className="font-medium text-sm text-foreground">💡 证据材料管理</h3>
              <p className="text-xs text-muted-foreground mt-1">
                点击“创建案件”后，系统会自动跳转至案件详情页。届时您可以在“证据”标签页中使用弹窗选择器（支持文件夹选取），一键批量上传您的全部证据材料。
              </p>
            </div>

            <div className="flex justify-end gap-2"><Button variant="outline" type="button" onClick={() => navigate(-1)}>取消</Button><Button type="submit" disabled={createCase.isPending}>{createCase.isPending ? '创建中...' : '创建案件'}</Button></div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
