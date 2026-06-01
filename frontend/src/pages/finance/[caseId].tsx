import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useFinanceOverview, useExpenses, useCostAnalysis, useWinRate, useCreateExpense, useDeleteExpense, useAssessWinRate } from '@/api/finance.api';
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
import { LegalDisclaimer } from '@/components/common/legal-disclaimer';
import { Plus, Trash2, TrendingUp, TrendingDown, DollarSign, PieChart, Sparkles, Target } from 'lucide-react';
import type { ExpenseRecord } from '@/types/finance.types';

const CATEGORY_MAP: Record<string, string> = {
  court_fee: '诉讼费',
  lawyer_fee: '律师费',
  evidence_fee: '证据费',
  travel_fee: '差旅费',
  consultation_fee: '咨询费',
  document_fee: '文书费',
  execution_fee: '执行费',
  other: '其他',
};

const STATUS_MAP: Record<string, string> = {
  pending: '待支付',
  paid: '已支付',
  reimbursed: '已报销',
  refunded: '已退还',
};

export default function FinancePage() {
  const { caseId } = useParams<{ caseId: string }>();
  const effectiveCaseId = caseId || '';

  const [expenseDialog, setExpenseDialog] = useState(false);
  const [expenseForm, setExpenseForm] = useState<Partial<ExpenseRecord>>({ title: '', amount: 0, currency: 'CNY', status: 'pending', category: 'other' });

  const { data: overview, isLoading: loadingOverview } = useFinanceOverview(effectiveCaseId);
  const { data: expensesData } = useExpenses(effectiveCaseId);
  const { data: costAnalysis } = useCostAnalysis(effectiveCaseId);
  const { data: winRateData } = useWinRate(effectiveCaseId);

  const createExpense = useCreateExpense(effectiveCaseId);
  const deleteExpense = useDeleteExpense(effectiveCaseId);
  const assessWinRate = useAssessWinRate(effectiveCaseId);

  const expenses = expensesData?.expenses || [];

  if (loadingOverview) return <PageSkeleton />;

  const finance = overview?.finance;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">案件财务</h1>
          <p className="text-sm text-muted-foreground mt-1">费用管理、成本分析和诉讼风险评估</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => assessWinRate.mutate(true)} disabled={assessWinRate.isPending}>
            <Sparkles className="mr-1 h-4 w-4" />{assessWinRate.isPending ? '评估中...' : 'AI 评估诉讼风险'}
          </Button>
          <Dialog open={expenseDialog} onOpenChange={setExpenseDialog}>
            <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加费用</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>添加费用记录</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2"><Label>费用标题</Label><Input value={expenseForm.title || ''} onChange={(e) => setExpenseForm({ ...expenseForm, title: e.target.value })} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>金额</Label><Input type="number" value={expenseForm.amount || ''} onChange={(e) => setExpenseForm({ ...expenseForm, amount: parseFloat(e.target.value) })} /></div>
                  <div className="space-y-2"><Label>类别</Label>
                    <Select value={expenseForm.category} onValueChange={(v) => setExpenseForm({ ...expenseForm, category: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {Object.entries(CATEGORY_MAP).map(([k, v]) => (<SelectItem key={k} value={k}>{v}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>状态</Label>
                    <Select value={expenseForm.status} onValueChange={(v) => setExpenseForm({ ...expenseForm, status: v as ExpenseRecord['status'] })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="pending">待支付</SelectItem><SelectItem value="paid">已支付</SelectItem><SelectItem value="reimbursed">已报销</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2"><Label>收款方</Label><Input value={expenseForm.payee || ''} onChange={(e) => setExpenseForm({ ...expenseForm, payee: e.target.value })} /></div>
                </div>
                <div className="space-y-2"><Label>描述</Label><Textarea value={expenseForm.description || ''} onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })} rows={2} /></div>
                <Button onClick={async () => { if (!expenseForm.title || !expenseForm.amount) return; await createExpense.mutateAsync(expenseForm); setExpenseDialog(false); setExpenseForm({ title: '', amount: 0, currency: 'CNY', status: 'pending', category: 'other' }); }} disabled={createExpense.isPending} className="w-full">{createExpense.isPending ? '创建中...' : '添加费用'}</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {finance && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-6"><div className="flex items-center gap-2"><DollarSign className="h-5 w-5 text-muted-foreground" /><div className="text-2xl font-bold">¥{finance.total_expenses.toLocaleString()}</div></div><p className="text-xs text-muted-foreground">总费用</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-green-600">¥{finance.total_paid.toLocaleString()}</div><p className="text-xs text-muted-foreground">已支付</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-amber-600">¥{finance.total_pending.toLocaleString()}</div><p className="text-xs text-muted-foreground">待支付</p></CardContent></Card>
          {finance.win_rate !== null && finance.win_rate !== undefined && (
            <Card><CardContent className="pt-6"><div className="text-2xl font-bold text-blue-600">{finance.win_rate}%</div><p className="text-xs text-muted-foreground">裁判支持度参考</p></CardContent></Card>
          )}
        </div>
      )}

      {costAnalysis && costAnalysis.cost_benefit_ratio !== undefined && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><PieChart className="h-5 w-5" />成本收益分析</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-muted-foreground">成本收益比</p>
              <p className="text-xl font-bold">{costAnalysis.cost_benefit_ratio.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">净收益</p>
              <div className="flex items-center gap-1">
                {costAnalysis.net_benefit !== undefined && costAnalysis.net_benefit >= 0 ? <TrendingUp className="h-4 w-4 text-green-500" /> : <TrendingDown className="h-4 w-4 text-red-500" />}
                <p className={`text-xl font-bold ${costAnalysis.net_benefit !== undefined && costAnalysis.net_benefit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ¥{costAnalysis.net_benefit?.toLocaleString() || '0'}
                </p>
              </div>
            </div>
            {costAnalysis.roi !== undefined && (
              <div>
                <p className="text-sm text-muted-foreground">投资回报率</p>
                <p className="text-xl font-bold">{costAnalysis.roi.toFixed(1)}%</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">费用笔数</p>
              <p className="text-xl font-bold">{costAnalysis.expense_count}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="expenses" className="space-y-4">
        <TabsList>
          <TabsTrigger value="expenses">费用记录 ({expenses.length})</TabsTrigger>
          <TabsTrigger value="breakdown">费用分类</TabsTrigger>
          {winRateData && <TabsTrigger value="winrate">风险评估</TabsTrigger>}
        </TabsList>

        <TabsContent value="expenses" className="space-y-3">
          {!expenses.length ? (
            <EmptyState title="暂无费用记录" description="添加费用来跟踪案件成本" />
          ) : (
            expenses.map((exp) => (
              <Card key={exp.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{exp.title}</span>
                        {exp.category && <Badge variant="outline">{CATEGORY_MAP[exp.category] || exp.category}</Badge>}
                        <Badge variant={exp.status === 'paid' ? 'default' : exp.status === 'reimbursed' ? 'secondary' : 'outline'}>
                          {STATUS_MAP[exp.status] || exp.status}
                        </Badge>
                      </div>
                      <div className="flex gap-4 text-sm text-muted-foreground">
                        {exp.expense_date && <span>{new Date(exp.expense_date).toLocaleDateString('zh-CN')}</span>}
                        {exp.payee && <span>收款方: {exp.payee}</span>}
                        {exp.invoice_number && <span>发票: {exp.invoice_number}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold">¥{exp.amount.toLocaleString()}</span>
                      <Button variant="ghost" size="sm" onClick={() => deleteExpense.mutate(exp.id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="breakdown">
          {overview?.expenses_by_category && Object.keys(overview.expenses_by_category).length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(overview.expenses_by_category).map(([cat, data]) => (
                <Card key={cat}>
                  <CardContent className="pt-6">
                    <p className="text-sm text-muted-foreground">{CATEGORY_MAP[cat] || cat}</p>
                    <p className="text-xl font-bold mt-1">¥{data.total.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">{data.count} 笔</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState title="暂无分类数据" description="添加费用后自动生成分类统计" />
          )}
        </TabsContent>

        <TabsContent value="winrate">
          {winRateData ? (
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-5 w-5" />诉讼风险评估</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <LegalDisclaimer variant="analysis" compact />
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-blue-600">{winRateData.win_rate ?? '—'}%</div>
                    <p className="text-sm text-muted-foreground mt-1">裁判支持度参考</p>
                  </div>
                  {winRateData.win_rate_confidence !== undefined && winRateData.win_rate_confidence !== null && (
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-600">{winRateData.win_rate_confidence}%</div>
                      <p className="text-sm text-muted-foreground mt-1">评估置信度</p>
                    </div>
                  )}
                </div>
                {winRateData.latest_assessment?.overall_analysis && (
                  <div>
                    <h4 className="font-medium mb-2">综合分析</h4>
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">{winRateData.latest_assessment.overall_analysis}</p>
                  </div>
                )}
                {winRateData.latest_assessment?.key_risks && winRateData.latest_assessment.key_risks.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">关键风险</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                      {winRateData.latest_assessment.key_risks.map((risk, i) => (<li key={i}>{risk}</li>))}
                    </ul>
                  </div>
                )}
                {winRateData.win_rate_assessed_at && (
                  <p className="text-xs text-muted-foreground">评估时间: {new Date(winRateData.win_rate_assessed_at).toLocaleString('zh-CN')}</p>
                )}
              </CardContent>
            </Card>
          ) : (
            <EmptyState title="暂无风险评估" description={'点击"AI 评估诉讼风险"生成评估报告'} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
