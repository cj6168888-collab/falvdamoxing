import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Target, Plus, Trash2, Edit, Sparkles, 
  FileText, ChevronRight, AlertTriangle, CheckCircle,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';


export interface CaseClaim {
  id: number;
  case_id: number;
  title: string;
  description?: string;
  claim_type?: string;
  amount?: string;
  priority: number;
  status: string;
  required_documents: string[];
  required_evidence_ids: string[];
  depends_on: number[];
  ai_plan_result?: string;
  ai_evidence_suggestions: string[];
  ai_document_suggestions: string[];
  risk_level: string;
  risk_notes?: string;
  notes?: string;
  created_at?: string;
  document_count: number;
  evidence_count: number;
}

interface CaseClaimsProps {
  caseId: number;
}

export function CaseClaims({ caseId }: CaseClaimsProps) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingClaim, setEditingClaim] = useState<CaseClaim | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    claim_type: '',
    amount: '',
    priority: 3,
  });

  const { data: claims, isLoading } = useQuery({
    queryKey: ['claims', caseId],
    queryFn: async () => {
      const res = await axiosInstance.get<CaseClaim[]>(`/api/claims/case/${caseId}`);
      return res.data || [];
    },
    enabled: !!caseId,
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData & { case_id: number }) => {
      const res = await axiosInstance.post('/api/claims', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims', caseId] });
      setShowForm(false);
      resetForm();
      toast.success('战役创建成功');
    },
    onError: () => {
      toast.error('创建失败');
    },
  });

  const planMutation = useMutation({
    mutationFn: async (claimId: number) => {
      const res = await axiosInstance.post(`/api/claims/${claimId}/plan`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims', caseId] });
      toast.success('AI 规划完成');
    },
    onError: () => {
      toast.error('规划失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (claimId: number) => {
      const res = await axiosInstance.delete(`/api/claims/${claimId}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims', caseId] });
      toast.success('战役已删除');
    },
  });

  const activateMutation = useMutation({
    mutationFn: async (claimId: number) => {
      const res = await axiosInstance.post(`/api/claims/${claimId}/activate`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims', caseId] });
    },
  });

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      claim_type: '',
      amount: '',
      priority: 3,
    });
    setEditingClaim(null);
  };

  const handleSubmit = () => {
    if (!formData.title.trim()) {
      toast.error('请输入战役名称');
      return;
    }
    createMutation.mutate({
      ...formData,
      case_id: caseId,
    });
  };

  const handleEdit = (claim: CaseClaim) => {
    setEditingClaim(claim);
    setFormData({
      title: claim.title,
      description: claim.description || '',
      claim_type: claim.claim_type || '',
      amount: claim.amount || '',
      priority: claim.priority,
    });
    setShowForm(true);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case '进行中':
        return <Badge variant="default" className="bg-blue-600">进行中</Badge>;
      case '已完成':
        return <Badge variant="secondary" className="bg-green-600">已完成</Badge>;
      case '已放弃':
        return <Badge variant="destructive">已放弃</Badge>;
      default:
        return <Badge variant="outline">待处理</Badge>;
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 1: return '紧急';
      case 2: return '高';
      case 3: return '中';
      case 4: return '低';
      default: return '待定';
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'high':
        return <Badge variant="destructive" className="text-xs"><AlertTriangle className="w-3 h-3 mr-1" />高风险</Badge>;
      case 'medium':
        return <Badge variant="outline" className="text-xs text-amber-600"><AlertTriangle className="w-3 h-3 mr-1" />中风险</Badge>;
      case 'low':
        return <Badge variant="secondary" className="text-xs bg-green-600"><CheckCircle className="w-3 h-3 mr-1" />低风险</Badge>;
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-16 rounded bg-muted" />
            <div className="h-16 rounded bg-muted" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">战役列表</CardTitle>
            <Badge variant="secondary">{claims?.length || 0}</Badge>
          </div>
          <Dialog open={showForm} onOpenChange={(open) => { setShowForm(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="w-4 h-4 mr-1" />
                新建战役
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingClaim ? '编辑战役' : '新建战役'}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="title">战役名称 *</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="例如：主张欠款本金"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">战役描述</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="详细描述此战役的目标和背景"
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="claim_type">诉求类型</Label>
                    <Input
                      id="claim_type"
                      value={formData.claim_type}
                      onChange={(e) => setFormData({ ...formData, claim_type: e.target.value })}
                      placeholder="如：欠款、违约金"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="amount">涉及金额</Label>
                    <Input
                      id="amount"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      placeholder="如：10万元"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="priority">优先级</Label>
                  <Select
                    value={String(formData.priority)}
                    onValueChange={(value) => setFormData({ ...formData, priority: parseInt(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">紧急</SelectItem>
                      <SelectItem value="2">高</SelectItem>
                      <SelectItem value="3">中</SelectItem>
                      <SelectItem value="4">低</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => { setShowForm(false); resetForm(); }}>取消</Button>
                <Button onClick={handleSubmit} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingClaim ? '保存' : '创建'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {(!claims || claims.length === 0) ? (
          <div className="text-center py-8">
            <Target className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-2 text-muted-foreground">暂无战役</p>
            <p className="text-sm text-muted-foreground">创建一个战役来管理您的诉讼请求</p>
          </div>
        ) : (
          <div className="space-y-3">
            {claims.map((claim) => (
              <Card 
                key={claim.id} 
                className={`cursor-pointer hover:shadow-md transition-all ${
                  claim.status === '进行中' ? 'border-primary bg-primary/5' : ''
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{claim.title}</span>
                        {getStatusBadge(claim.status)}
                        {getRiskBadge(claim.risk_level)}
                      </div>
                      {claim.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                          {claim.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        {claim.claim_type && <span>类型: {claim.claim_type}</span>}
                        {claim.amount && <span>金额: {claim.amount}</span>}
                        <span>优先级: {getPriorityLabel(claim.priority)}</span>
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" /> 文书: {claim.document_count}
                        </span>
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" /> 证据: {claim.evidence_count}
                        </span>
                      </div>
                      {claim.required_documents && claim.required_documents.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {claim.required_documents.slice(0, 4).map((doc, i) => (
                            <Badge key={i} variant="outline" className="text-xs">{doc}</Badge>
                          ))}
                          {claim.required_documents.length > 4 && (
                            <Badge variant="outline" className="text-xs">+{claim.required_documents.length - 4}</Badge>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          planMutation.mutate(claim.id);
                        }}
                        disabled={planMutation.isPending}
                        title="AI 规划"
                      >
                        {planMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEdit(claim);
                        }}
                        title="编辑"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm('确定删除此战役？')) {
                            deleteMutation.mutate(claim.id);
                          }
                        }}
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                      {claim.status === '待处理' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            activateMutation.mutate(claim.id);
                          }}
                          title="激活"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
