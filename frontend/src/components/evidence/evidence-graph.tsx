import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import {
  analyzeEvidenceRelationships,
  askEvidenceQuestion,
  getEvidenceGraph,
  useEvidence,
  type EvidenceGraphNode,
  type EvidenceQuestionResponse,
} from '@/api/evidence.api';
import { Database, Loader2, MessageSquare, Network, RefreshCw, Search } from 'lucide-react';
import { toast } from 'sonner';

interface Props { caseId: string; }

function getNodeName(node: EvidenceGraphNode) {
  return node.label || node.name || node.title || node.id;
}

function getNodeScore(node: EvidenceGraphNode) {
  const score = node.credibility_score ?? node.credibility ?? node.strength;
  if (typeof score !== 'number') return null;
  return score <= 1 ? Math.round(score * 100) : Math.round(score);
}

function getEvidenceName(evidence: Record<string, unknown>) {
  return String(evidence.display_name || evidence.original_filename || evidence.name || evidence.id || '未命名证据');
}

export function EvidenceGraph({ caseId }: Props) {
  const [question, setQuestion] = useState('这份证据能证明什么？');
  const [qaResult, setQaResult] = useState<EvidenceQuestionResponse | null>(null);
  const { data: evidenceList = [], isLoading: evidenceLoading } = useEvidence(caseId);
  const graphQuery = useQuery({
    queryKey: ['evidence-graph-data', caseId],
    queryFn: () => getEvidenceGraph(caseId),
    enabled: !!caseId,
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeEvidenceRelationships(caseId),
    onSuccess: async () => {
      await graphQuery.refetch();
      toast.success('证据关系已刷新');
    },
    onError: () => toast.error('证据关系分析失败'),
  });

  const qaMutation = useMutation({
    mutationFn: () => askEvidenceQuestion(caseId, question),
    onSuccess: (result) => setQaResult(result),
    onError: () => toast.error('证据问答失败'),
  });

  const graph = graphQuery.data;
  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];
  const summary = graph?.summary || {};
  const evidenceCount = evidenceList.length;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">证据图谱</h2>
          <p className="text-sm text-muted-foreground">证据节点、关系链路和单案证据问答</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => graphQuery.refetch()} disabled={graphQuery.isFetching}>
            {graphQuery.isFetching ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            刷新图谱
          </Button>
          <Button size="sm" onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending || !caseId}>
            {analyzeMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Network className="mr-2 h-4 w-4" />}
            分析关系
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">已索引证据</p>
            <p className="mt-1 text-2xl font-semibold">{evidenceCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">图谱节点</p>
            <p className="mt-1 text-2xl font-semibold">{nodes.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">关系边</p>
            <p className="mt-1 text-2xl font-semibold">{edges.length}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Database className="h-4 w-4" />
              图谱节点
            </CardTitle>
          </CardHeader>
          <CardContent>
            {graphQuery.isLoading || evidenceLoading ? (
              <div className="h-48 animate-pulse rounded-md bg-muted" />
            ) : nodes.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {nodes.map((node) => {
                  const score = getNodeScore(node);
                  return (
                    <div key={node.id} className="rounded-md border p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{getNodeName(node)}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{node.category || node.type || '证据'}</p>
                        </div>
                        {node.status && <Badge variant="secondary">{node.status}</Badge>}
                      </div>
                      {score !== null && (
                        <div className="mt-3">
                          <div className="mb-1 flex justify-between text-xs text-muted-foreground">
                            <span>可信度/强度</span>
                            <span>{score}%</span>
                          </div>
                          <Progress value={score} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex h-48 items-center justify-center rounded-md border bg-muted/20 text-sm text-muted-foreground">
                暂无图谱节点，请先上传或索引证据
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Network className="h-4 w-4" />
              关系链路
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {edges.length > 0 ? (
              edges.slice(0, 8).map((edge, index) => (
                <div key={edge.id || `${edge.source}-${edge.target}-${index}`} className="rounded-md border p-3 text-sm">
                  <div className="font-medium">{edge.source} {'->'} {edge.target}</div>
                  <p className="mt-1 text-xs text-muted-foreground">{edge.label || edge.type || '关联关系'}</p>
                </div>
              ))
            ) : (
              <p className="rounded-md border p-3 text-sm text-muted-foreground">暂无自动关系，可点击“分析关系”刷新。</p>
            )}
            {Object.keys(summary).length > 0 && (
              <div className="rounded-md bg-muted/40 p-3 text-xs text-muted-foreground">
                {Object.entries(summary).slice(0, 6).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3">
                    <span>{key}</span>
                    <span>{String(value)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <MessageSquare className="h-4 w-4" />
            证据问答
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {evidenceList.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {evidenceList.slice(0, 6).map((item) => {
                const evidence = item as unknown as Record<string, unknown>;
                return <Badge key={String(evidence.id)} variant="outline">{getEvidenceName(evidence)}</Badge>;
              })}
            </div>
          )}
          <Textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="围绕当前案件证据提问"
            className="min-h-24"
          />
          <Button onClick={() => qaMutation.mutate()} disabled={qaMutation.isPending || !question.trim()}>
            {qaMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
            提交证据问题
          </Button>
          {qaResult && (
            <div data-testid="evidence-qa-answer" className="rounded-md border bg-muted/20 p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge variant={qaResult.needs_redirect ? 'destructive' : 'secondary'}>
                  {qaResult.topic_analysis?.scope || qaResult.status || '已回答'}
                </Badge>
                {typeof qaResult.topic_analysis?.relevance_score === 'number' && (
                  <span className="text-xs text-muted-foreground">
                    相关度 {Math.round(qaResult.topic_analysis.relevance_score * 100)}%
                  </span>
                )}
              </div>
              <p className="whitespace-pre-wrap text-sm">{qaResult.answer || qaResult.message || qaResult.redirect_suggestion || '暂无回答'}</p>
              {qaResult.topic_analysis?.reason && (
                <p className="mt-2 text-xs text-muted-foreground">{qaResult.topic_analysis.reason}</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
