import { useState } from 'react';
import { useAppeals, useCreateAppeal, useAppealStatistics, generateAppealPetition } from '@/api/appeal.api';
import { useAppealArguments, useCreateAppealArgument, useDeleteAppealArgument } from '@/api/appeal.api';
import { useAppealDeadlines, useCreateAppealDeadline } from '@/api/appeal.api';
import { useAppealDocuments, useCreateAppealDocument } from '@/api/appeal.api';
import { useAppealStrategy } from '@/api/appeal.api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Plus, FileText, Clock, Target, Shield, AlertTriangle, CheckCircle2, Trash2, Sparkles, ChevronRight } from 'lucide-react';
import type { Appeal, AppealArgument, AppealDeadline, AppealDocument } from '@/types/appeal.types';

const APPEAL_TYPE_MAP: Record<string, string> = {
  first_to_second: '一审到二审',
  second_to_retrial: '二审到再审',
  retrial: '再审申请',
};

const APPEAL_REASON_MAP: Record<string, string> = {
  factual_error: '事实认定错误',
  legal_error: '法律适用错误',
  procedural: '程序违法',
  new_evidence: '新证据',
  insufficient: '证据不足',
  other: '其他',
};

const STATUS_MAP: Record<string, string> = {
  preparing: '准备中',
  submitted: '已提交',
  accepted: '已受理',
  hearing: '开庭审理',
  decided: '已判决',
  rejected: '被驳回',
  withdrawn: '已撤回',
};

const IMPORTANCE_MAP: Record<string, string> = { high: '高', medium: '中', low: '低' };

function getStatusBadge(status: string) {
  const variantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    preparing: 'outline', submitted: 'secondary', accepted: 'default',
    hearing: 'default', decided: 'outline', rejected: 'destructive', withdrawn: 'outline',
  };
  return <Badge variant={variantMap[status] || 'outline'}>{STATUS_MAP[status] || status}</Badge>;
}

function getImportanceBadge(importance: string) {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    low: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
  };
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors[importance] || colors.low}`}>{IMPORTANCE_MAP[importance] || importance}</span>;
}

// ============ Appeal Card ============

function AppealCard({ appeal, onSelect }: { appeal: Appeal; onSelect: () => void }) {
  return (
    <Card className="cursor-pointer hover:border-primary/50 transition-colors" onClick={onSelect}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{appeal.appellant_name || '未命名上诉人'}</span>
              {getStatusBadge(appeal.status)}
            </div>
            <p className="text-sm text-muted-foreground">
              {appeal.original_court ? `原审法院: ${appeal.original_court}` : '未填写原审法院'}
              {appeal.appeal_deadline && ` · 上诉期限: ${new Date(appeal.appeal_deadline).toLocaleDateString('zh-CN')}`}
            </p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            {appeal.days_remaining !== undefined && (
              <span className={appeal.is_overdue ? 'text-red-500 font-medium' : 'text-muted-foreground'}>
                {appeal.is_overdue ? '已过期' : `剩余 ${appeal.days_remaining} 天`}
              </span>
            )}
            <div className="flex gap-3 text-xs text-muted-foreground">
              <span>{appeal.argument_count || 0} 论点</span>
              <span>{appeal.document_count || 0} 材料</span>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============ Arguments Panel ============

function AppealArgumentsPanel({ appealId, caseId }: { appealId: number; caseId: string }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<AppealArgument>>({ importance: 'medium', status: 'draft', is_key_argument: false });

  const { data: argsData, isLoading } = useAppealArguments(caseId);
  const createMutation = useCreateAppealArgument(caseId);
  const deleteMutation = useDeleteAppealArgument(caseId);

  const arguments_ = argsData?.arguments?.filter((a) => a.appeal_record_id === appealId) || [];

  const handleCreate = async () => {
    if (!formData.title) return;
    await createMutation.mutateAsync({ ...formData, appeal_record_id: appealId });
    setDialogOpen(false);
    setFormData({ importance: 'medium', status: 'draft', is_key_argument: false });
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Target className="h-5 w-5" />上诉论点</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加论点</Button></DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader><DialogTitle>添加上诉论点</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>论点标题</Label><Input value={formData.title || ''} onChange={(e) => setFormData({ ...formData, title: e.target.value })} /></div>
              <div className="space-y-2"><Label>论点类型</Label>
                <Select value={formData.argument_type} onValueChange={(v) => setFormData({ ...formData, argument_type: v })}>
                  <SelectTrigger><SelectValue placeholder="选择类型" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="factual_error">事实错误</SelectItem>
                    <SelectItem value="legal_error">法律错误</SelectItem>
                    <SelectItem value="procedural">程序违法</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2"><Label>详细描述</Label><Textarea value={formData.description || ''} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={3} /></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>重要性</Label>
                  <Select value={formData.importance} onValueChange={(v) => setFormData({ ...formData, importance: v as AppealArgument['importance'] })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="high">高</SelectItem><SelectItem value="medium">中</SelectItem><SelectItem value="low">低</SelectItem></SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>支持度参考 (%)</Label><Input type="number" min={0} max={100} value={formData.success_probability || ''} onChange={(e) => setFormData({ ...formData, success_probability: parseFloat(e.target.value) })} /></div>
              </div>
              <div className="space-y-2"><Label>原审认定</Label><Textarea value={formData.original_finding || ''} onChange={(e) => setFormData({ ...formData, original_finding: e.target.value })} rows={2} /></div>
              <div className="space-y-2"><Label>上诉主张</Label><Textarea value={formData.appeal_finding || ''} onChange={(e) => setFormData({ ...formData, appeal_finding: e.target.value })} rows={2} /></div>
              <Button onClick={handleCreate} disabled={createMutation.isPending} className="w-full">{createMutation.isPending ? '创建中...' : '创建论点'}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {!arguments_.length ? (
        <EmptyState title="暂无上诉论点" description="添加论点来构建上诉论证体系" />
      ) : (
        <div className="space-y-3">
          {arguments_.map((arg) => (
            <Card key={arg.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{arg.title}</span>
                      {getImportanceBadge(arg.importance)}
                      {arg.is_key_argument && <Badge variant="destructive">核心论点</Badge>}
                    </div>
                    {arg.description && <p className="text-sm text-muted-foreground">{arg.description}</p>}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {arg.original_finding && <div><span className="text-muted-foreground">原审认定:</span> {arg.original_finding}</div>}
                      {arg.appeal_finding && <div><span className="text-muted-foreground">上诉主张:</span> {arg.appeal_finding}</div>}
                    </div>
                    {arg.success_probability !== undefined && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">支持度参考:</span>
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${arg.success_probability * 100}%` }} />
                        </div>
                        <span>{(arg.success_probability * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(arg.id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ============ Deadlines Panel ============

function AppealDeadlinePanel({ appealId }: { appealId: number }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<AppealDeadline>>({ is_mandatory: true, status: 'pending' });

  const { data: deadlinesData, isLoading } = useAppealDeadlines(String(appealId));
  const createMutation = useCreateAppealDeadline(String(appealId));

  const deadlines = deadlinesData?.deadlines || [];

  const handleCreate = async () => {
    if (!formData.deadline_type || !formData.deadline_name) return;
    await createMutation.mutateAsync(formData);
    setDialogOpen(false);
    setFormData({ is_mandatory: true, status: 'pending' });
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Clock className="h-5 w-5" />期限追踪</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加期限</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>添加上诉期限</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>期限名称</Label><Input value={formData.deadline_name || ''} onChange={(e) => setFormData({ ...formData, deadline_name: e.target.value })} /></div>
              <div className="space-y-2"><Label>截止日期</Label><Input type="datetime-local" value={formData.deadline_date || ''} onChange={(e) => setFormData({ ...formData, deadline_date: e.target.value })} /></div>
              <div className="space-y-2"><Label>法律依据</Label><Input value={formData.legal_basis || ''} onChange={(e) => setFormData({ ...formData, legal_basis: e.target.value })} placeholder="例如：《民事诉讼法》第XX条" /></div>
              <Button onClick={handleCreate} disabled={createMutation.isPending} className="w-full">{createMutation.isPending ? '创建中...' : '创建期限'}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {!deadlines.length ? (
        <EmptyState title="暂无期限记录" description="系统已自动创建上诉递交期限" />
      ) : (
        <div className="space-y-3">
          {deadlines.map((dl) => {
            const isOverdue = dl.status === 'expired' || (dl.days_remaining !== undefined && dl.days_remaining < 0);
            const isUrgent = dl.days_remaining !== undefined && dl.days_remaining >= 0 && dl.days_remaining <= 3;
            return (
              <Card key={dl.id} className={isOverdue ? 'border-red-200 dark:border-red-800' : isUrgent ? 'border-amber-200 dark:border-amber-800' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{dl.deadline_name}</span>
                        {dl.is_mandatory && <Badge variant="destructive">法定</Badge>}
                        {isOverdue && <Badge variant="destructive">已过期</Badge>}
                        {isUrgent && <Badge variant="outline" className="text-amber-600">紧急</Badge>}
                      </div>
                      {dl.deadline_date && <p className="text-sm text-muted-foreground">截止日期: {new Date(dl.deadline_date).toLocaleDateString('zh-CN')}</p>}
                      {dl.description && <p className="text-sm text-muted-foreground">{dl.description}</p>}
                      {dl.legal_basis && <p className="text-xs text-muted-foreground">{dl.legal_basis}</p>}
                    </div>
                    <div className="text-right">
                      {dl.days_remaining !== undefined && (
                        <div className={`text-lg font-bold ${isOverdue ? 'text-red-500' : isUrgent ? 'text-amber-500' : 'text-green-500'}`}>
                          {isOverdue ? '已过期' : `${dl.days_remaining} 天`}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============ Documents Panel ============

function AppealDocumentsPanel({ appealId }: { appealId: number }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<AppealDocument>>({ is_required: true, status: 'pending' });

  const { data: docsData, isLoading } = useAppealDocuments(String(appealId));
  const createMutation = useCreateAppealDocument(String(appealId));

  const documents = docsData?.documents || [];

  const handleCreate = async () => {
    if (!formData.document_type || !formData.document_name) return;
    await createMutation.mutateAsync(formData);
    setDialogOpen(false);
    setFormData({ is_required: true, status: 'pending' });
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2"><FileText className="h-5 w-5" />上诉材料</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加材料</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>添加上诉材料</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>材料名称</Label><Input value={formData.document_name || ''} onChange={(e) => setFormData({ ...formData, document_name: e.target.value })} /></div>
              <div className="space-y-2"><Label>材料类型</Label><Input value={formData.document_type || ''} onChange={(e) => setFormData({ ...formData, document_type: e.target.value })} placeholder="例如：证据材料/上诉状/原审判决书" /></div>
              <div className="space-y-2"><Label>用途说明</Label><Textarea value={formData.purpose || ''} onChange={(e) => setFormData({ ...formData, purpose: e.target.value })} rows={2} /></div>
              <Button onClick={handleCreate} disabled={createMutation.isPending} className="w-full">{createMutation.isPending ? '创建中...' : '添加材料'}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {!documents.length ? (
        <EmptyState title="暂无上诉材料" description="添加上诉状、证据材料等文件" />
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <Card key={doc.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{doc.document_name}</span>
                      {doc.is_required && <Badge variant="outline">必需</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground">{doc.document_type}{doc.purpose ? ` · ${doc.purpose}` : ''}</p>
                  </div>
                  <Badge variant={doc.status === 'prepared' ? 'default' : doc.status === 'submitted' ? 'secondary' : 'outline'}>
                    {doc.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ============ Strategy Panel ============

function AppealStrategyPanel({ appealId }: { appealId: number }) {
  const { data: strategy, isLoading } = useAppealStrategy(String(appealId));

  if (isLoading) return <PageSkeleton />;

  if (!strategy) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2"><Shield className="h-5 w-5" />二审策略</h3>
        <EmptyState title="暂无二审策略" description="创建答辩策略来应对上诉" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2"><Shield className="h-5 w-5" />二审策略</h3>
      <Card>
        <CardHeader><CardTitle>{strategy.title}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {strategy.defense_reasoning && <div><h4 className="font-medium mb-1">答辩论证</h4><p className="text-sm text-muted-foreground whitespace-pre-wrap">{strategy.defense_reasoning}</p></div>}
          {strategy.expected_outcome && <div><h4 className="font-medium mb-1">预期结果</h4><p className="text-sm text-muted-foreground">{strategy.expected_outcome}</p></div>}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">审批状态:</span>
            {strategy.is_approved ? <CheckCircle2 className="h-4 w-4 text-green-500" /> : <AlertTriangle className="h-4 w-4 text-amber-500" />}
            <span className="text-sm">{strategy.is_approved ? '已审批' : '待审批'}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============ Main Component ============

export function AppealOverview({ caseId }: { caseId: string }) {
  const [selectedAppealId, setSelectedAppealId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<Appeal>>({ appeal_type: 'first_to_second', appeal_reason: 'legal_error' });

  const { data: appealsData, isLoading: loadingAppeals } = useAppeals(caseId);
  const { data: stats } = useAppealStatistics(caseId);
  const createMutation = useCreateAppeal(caseId);

  const handleCreate = async () => {
    if (!formData.original_court || !formData.appellant_name) return;
    const result = await createMutation.mutateAsync(formData);
    setDialogOpen(false);
    setFormData({ appeal_type: 'first_to_second', appeal_reason: 'legal_error' });
    if (result?.appeal?.id) {
      setSelectedAppealId(result.appeal.id);
    }
  };

  if (loadingAppeals) return <PageSkeleton />;

  const appeals = appealsData?.appeals || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">上诉追踪</h1>
          <p className="text-sm text-muted-foreground mt-1">管理第二审程序的完整流程</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" />新建上诉</Button></DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader><DialogTitle>新建上诉记录</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>上诉类型</Label>
                  <Select value={formData.appeal_type} onValueChange={(v) => setFormData({ ...formData, appeal_type: v as Appeal['appeal_type'] })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{Object.entries(APPEAL_TYPE_MAP).map(([k, v]) => (<SelectItem key={k} value={k}>{v}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>上诉理由</Label>
                  <Select value={formData.appeal_reason} onValueChange={(v) => setFormData({ ...formData, appeal_reason: v as Appeal['appeal_reason'] })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{Object.entries(APPEAL_REASON_MAP).map(([k, v]) => (<SelectItem key={k} value={k}>{v}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2"><Label>原审法院</Label><Input value={formData.original_court || ''} onChange={(e) => setFormData({ ...formData, original_court: e.target.value })} placeholder="例如：XX市XX区人民法院" /></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>上诉人类型</Label><Input value={formData.appellant_type || ''} onChange={(e) => setFormData({ ...formData, appellant_type: e.target.value })} placeholder="原告/被告/第三人" /></div>
                <div className="space-y-2"><Label>上诉人姓名</Label><Input value={formData.appellant_name || ''} onChange={(e) => setFormData({ ...formData, appellant_name: e.target.value })} placeholder="上诉人姓名" /></div>
              </div>
              <div className="space-y-2"><Label>收到判决日期</Label><Input type="datetime-local" value={formData.judgment_received_date || ''} onChange={(e) => setFormData({ ...formData, judgment_received_date: e.target.value })} /></div>
              <div className="space-y-2"><Label>原审判决内容</Label><Textarea value={formData.original_judgment_content || ''} onChange={(e) => setFormData({ ...formData, original_judgment_content: e.target.value })} rows={4} placeholder="原审判决的主要内容..." /></div>
              <div className="space-y-2"><Label>上诉请求</Label><Textarea value={formData.appeal_requests || ''} onChange={(e) => setFormData({ ...formData, appeal_requests: e.target.value })} rows={3} placeholder="具体的上诉请求..." /></div>
              <Button onClick={handleCreate} disabled={createMutation.isPending} className="w-full">{createMutation.isPending ? '创建中...' : '创建上诉记录'}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.total_appeals}</div><p className="text-xs text-muted-foreground">上诉记录</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.total_arguments}</div><p className="text-xs text-muted-foreground">上诉论点</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.key_arguments}</div><p className="text-xs text-muted-foreground">核心论点</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.prepared_documents}/{stats.total_documents}</div><p className="text-xs text-muted-foreground">材料准备</p></CardContent></Card>
        </div>
      )}

      {!appeals.length ? (
        <EmptyState title="暂无上诉记录" description={'点击"新建上诉"开始创建上诉流程'} />
      ) : (
        <Tabs defaultValue={selectedAppealId ? 'detail' : 'list'} className="space-y-4">
          <TabsList>
            <TabsTrigger value="list">上诉记录 ({appeals.length})</TabsTrigger>
            {selectedAppealId && <TabsTrigger value="detail">上诉详情</TabsTrigger>}
          </TabsList>

          <TabsContent value="list" className="space-y-3">
            {appeals.map((appeal) => (
              <AppealCard key={appeal.id} appeal={appeal} onSelect={() => setSelectedAppealId(appeal.id)} />
            ))}
          </TabsContent>

          <TabsContent value="detail">
            {selectedAppealId && (
              <Tabs defaultValue="arguments" className="space-y-4">
                <div className="flex items-center justify-between">
                  <TabsList>
                    <TabsTrigger value="arguments">上诉论点</TabsTrigger>
                    <TabsTrigger value="deadlines">期限追踪</TabsTrigger>
                    <TabsTrigger value="documents">上诉材料</TabsTrigger>
                    <TabsTrigger value="strategy">二审策略</TabsTrigger>
                  </TabsList>
                  <Button variant="outline" size="sm" onClick={() => {
                    generateAppealPetition(String(selectedAppealId)).then(() => {});
                  }}><Sparkles className="mr-1 h-4 w-4" />AI 生成上诉状</Button>
                </div>
                <TabsContent value="arguments"><AppealArgumentsPanel appealId={selectedAppealId} caseId={caseId} /></TabsContent>
                <TabsContent value="deadlines"><AppealDeadlinePanel appealId={selectedAppealId} /></TabsContent>
                <TabsContent value="documents"><AppealDocumentsPanel appealId={selectedAppealId} /></TabsContent>
                <TabsContent value="strategy"><AppealStrategyPanel appealId={selectedAppealId} /></TabsContent>
              </Tabs>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
