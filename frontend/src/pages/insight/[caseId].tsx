import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  AlertCircle,
  BrainCircuit,
  Database,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { toast } from 'sonner';

import {
  answerInsightClarification,
  askInsightQuestion,
  buildInsightEvidenceGraph,
  clearInsightCache,
  generateInsightReport,
  getInsightReportStatus,
  queryInsightEvidence,
  type EvidenceGraphNode,
  type EvidenceGraphResponse,
  type EvidenceQueryResponse,
  type InsightQuestionResponse,
  type InsightReportResponse,
  type InsightReportStatus,
} from '@/api/insight.api';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

type BusyKey = 'question' | 'clarification' | 'report' | 'status' | 'graph' | 'query' | 'cache' | null;

function getErrorMessage(error: unknown, fallback: string) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string; message?: string } } }).response;
    return response?.data?.detail || response?.data?.message || fallback;
  }
  return error instanceof Error ? error.message : fallback;
}

function formatQuestion(question: string | { question?: string; options?: string[] }) {
  if (typeof question === 'string') return question;
  if (question.options?.length) return `${question.question || '需要补充信息'}：${question.options.join(' / ')}`;
  return question.question || '需要补充信息';
}

function renderList(items?: string[]) {
  if (!items?.length) return <span className="text-muted-foreground">暂无</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <Badge key={item} variant="outline">{item}</Badge>
      ))}
    </div>
  );
}

function EvidenceNodeCard({ node }: { node: EvidenceGraphNode }) {
  const score = typeof node.credibility === 'number' ? Math.round(node.credibility * 100) : null;
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate font-medium">{node.name}</p>
            <p className="text-sm text-muted-foreground">{node.type}</p>
          </div>
          {score !== null && <Badge variant={score >= 80 ? 'default' : 'secondary'}>信度 {score}%</Badge>}
        </div>
        <div className="space-y-1 text-sm">
          <p className="font-medium">证明事实</p>
          {renderList(node.proves_facts)}
        </div>
        <div className="space-y-1 text-sm">
          <p className="font-medium">关键词</p>
          {renderList(node.keywords)}
        </div>
      </CardContent>
    </Card>
  );
}

export default function InsightPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [busy, setBusy] = useState<BusyKey>(null);

  const [question, setQuestion] = useState('下一步诉讼策略是什么？');
  const [questionResult, setQuestionResult] = useState<InsightQuestionResponse | null>(null);
  const [clarification, setClarification] = useState('');

  const [reportType, setReportType] = useState('analysis');
  const [forceReport, setForceReport] = useState(false);
  const [report, setReport] = useState<InsightReportResponse | null>(null);
  const [reportStatus, setReportStatus] = useState<InsightReportStatus | null>(null);

  const [graph, setGraph] = useState<EvidenceGraphResponse | null>(null);
  const [queryText, setQueryText] = useState('付款');
  const [queryType, setQueryType] = useState('all');
  const [queryResult, setQueryResult] = useState<EvidenceQueryResponse | null>(null);
  const [cacheMessage, setCacheMessage] = useState('');

  const currentCaseId = caseId || '';

  const runWithBusy = async (key: BusyKey, action: () => Promise<void>, successMessage?: string) => {
    if (!currentCaseId) return;
    setBusy(key);
    try {
      await action();
      if (successMessage) toast.success(successMessage);
    } catch (error) {
      toast.error(getErrorMessage(error, '操作失败'));
    } finally {
      setBusy(null);
    }
  };

  const handleAsk = () => runWithBusy('question', async () => {
    setQuestionResult(await askInsightQuestion(currentCaseId, question));
  });

  const handleClarify = () => runWithBusy('clarification', async () => {
    setQuestionResult(await answerInsightClarification(currentCaseId, question, { 补充说明: clarification }));
  });

  const handleGenerateReport = () => runWithBusy('report', async () => {
    const nextReport = await generateInsightReport(currentCaseId, reportType, forceReport);
    setReport(nextReport);
    setReportStatus(null);
  }, '增强报告已生成');

  const handleRefreshStatus = () => runWithBusy('status', async () => {
    setReportStatus(await getInsightReportStatus(currentCaseId, reportType));
  });

  const handleBuildGraph = () => runWithBusy('graph', async () => {
    setGraph(await buildInsightEvidenceGraph(currentCaseId, true));
  }, '证据图谱已刷新');

  const handleQueryEvidence = () => runWithBusy('query', async () => {
    setQueryResult(await queryInsightEvidence(currentCaseId, queryText, queryType));
  });

  const handleClearCache = () => runWithBusy('cache', async () => {
    const result = await clearInsightCache(currentCaseId);
    setCacheMessage(result.message);
  }, '增强分析缓存已清除');

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <BrainCircuit className="h-6 w-6 text-primary" />
            增强分析
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">智能问答、分段报告、证据图谱和信度检索</p>
        </div>
        <Button variant="outline" onClick={handleClearCache} disabled={busy === 'cache'}>
          {busy === 'cache' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          清除缓存
        </Button>
      </div>

      {cacheMessage && (
        <Alert variant="success">
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>缓存状态</AlertTitle>
          <AlertDescription>{cacheMessage}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="question" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="question"><MessageSquare className="mr-2 h-4 w-4" />智能问答</TabsTrigger>
          <TabsTrigger value="report"><BrainCircuit className="mr-2 h-4 w-4" />分段报告</TabsTrigger>
          <TabsTrigger value="evidence"><Database className="mr-2 h-4 w-4" />证据图谱</TabsTrigger>
        </TabsList>

        <TabsContent value="question" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>智能问答</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="insight-question">问题</Label>
                <Textarea
                  id="insight-question"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  rows={4}
                />
              </div>
              <Button onClick={handleAsk} disabled={busy === 'question' || !question.trim()}>
                {busy === 'question' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                提交问题
              </Button>
            </CardContent>
          </Card>

          {questionResult && (
            <Card>
              <CardHeader>
                <CardTitle>问答结果</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <p className="text-sm font-medium">意图</p>
                    <p className="text-sm text-muted-foreground">{questionResult.intent || '未识别'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">关键实体</p>
                    {renderList(questionResult.key_entities)}
                  </div>
                </div>
                {questionResult.needs_clarification && (
                  <Alert variant="warning">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>需要补充信息</AlertTitle>
                    <AlertDescription>
                      <ul className="list-disc space-y-1 pl-5">
                        {(questionResult.clarifying_questions || []).map((item, index) => (
                          <li key={`${formatQuestion(item)}-${index}`}>{formatQuestion(item)}</li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
                {questionResult.answer && (
                  <div className="rounded-md border bg-muted/30 p-4 text-sm leading-7 whitespace-pre-wrap">
                    {questionResult.answer}
                  </div>
                )}
                {questionResult.needs_clarification && (
                  <div className="space-y-2">
                    <Label htmlFor="insight-clarification">补充说明</Label>
                    <Textarea
                      id="insight-clarification"
                      value={clarification}
                      onChange={(event) => setClarification(event.target.value)}
                      rows={3}
                    />
                    <Button onClick={handleClarify} disabled={busy === 'clarification' || !clarification.trim()}>
                      {busy === 'clarification' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      提交补充
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="report" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>分段报告</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-[220px_1fr]">
                <div className="space-y-2">
                  <Label>报告类型</Label>
                  <Select value={reportType} onValueChange={setReportType}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="analysis">案件分析</SelectItem>
                      <SelectItem value="strategy">策略建议</SelectItem>
                      <SelectItem value="full_analysis">完整对抗分析</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end gap-3">
                  <label className="flex h-10 items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={forceReport}
                      onChange={(event) => setForceReport(event.target.checked)}
                    />
                    强制重新生成
                  </label>
                  <Button onClick={handleGenerateReport} disabled={busy === 'report'}>
                    {busy === 'report' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    生成报告
                  </Button>
                  <Button variant="outline" onClick={handleRefreshStatus} disabled={busy === 'status'}>
                    {busy === 'status' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    刷新状态
                  </Button>
                </div>
              </div>
              {reportStatus && (
                <div className="space-y-2 rounded-md border p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span>状态：{reportStatus.status}</span>
                    <span>{Math.round((reportStatus.progress || 0) * 100)}%</span>
                  </div>
                  <Progress value={(reportStatus.progress || 0) * 100} />
                </div>
              )}
            </CardContent>
          </Card>

          {report && (
            <Card>
              <CardHeader>
                <CardTitle>报告内容</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2 text-sm">
                  <Badge variant="outline">{report.report_type}</Badge>
                  <Badge variant="outline">{report.word_count} 字符</Badge>
                  <Badge variant="outline">{report.segments.length} 个进度片段</Badge>
                </div>
                <div className="max-h-[520px] overflow-y-auto rounded-md border bg-muted/30 p-4 text-sm leading-7 whitespace-pre-wrap">
                  {report.content}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="evidence" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>证据图谱</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-3">
                <Button onClick={handleBuildGraph} disabled={busy === 'graph'}>
                  {busy === 'graph' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Database className="mr-2 h-4 w-4" />}
                  构建图谱
                </Button>
              </div>

              {graph?.message && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>图谱结果</AlertTitle>
                  <AlertDescription>{graph.message}</AlertDescription>
                </Alert>
              )}

              {graph && !graph.message && (
                <div className="grid gap-3 md:grid-cols-3">
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-2xl font-bold">{graph.total_evidence || graph.nodes.length}</p>
                      <p className="text-sm text-muted-foreground">证据节点</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-2xl font-bold">{String(graph.summary?.high_credibility_count ?? 0)}</p>
                      <p className="text-sm text-muted-foreground">高信度</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-2xl font-bold">{String(graph.summary?.low_credibility_count ?? 0)}</p>
                      <p className="text-sm text-muted-foreground">低信度</p>
                    </CardContent>
                  </Card>
                </div>
              )}

              {graph?.nodes?.length ? (
                <div className="grid gap-3 lg:grid-cols-2">
                  {graph.nodes.map((node) => <EvidenceNodeCard key={node.id} node={node} />)}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>证据检索</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-[1fr_180px_auto]">
                <Input value={queryText} onChange={(event) => setQueryText(event.target.value)} placeholder="输入关键词" />
                <Select value={queryType} onValueChange={setQueryType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全局检索</SelectItem>
                    <SelectItem value="keywords">关键词</SelectItem>
                    <SelectItem value="related">相关证据</SelectItem>
                    <SelectItem value="contradicts">矛盾证据</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={handleQueryEvidence} disabled={busy === 'query' || !queryText.trim()}>
                  {busy === 'query' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                  查询
                </Button>
              </div>

              {queryResult && (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    查询「{queryResult.query}」返回 {queryResult.count} 条结果
                  </p>
                  {queryResult.results.map((node) => <EvidenceNodeCard key={node.id} node={node} />)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
