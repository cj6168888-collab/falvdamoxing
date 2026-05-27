import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { useAnswerGuideQuestion, useEvidenceGuideHook } from '@/hooks/use-evidence-guide';
import type { EvidenceGuideGap, EvidenceGuideQuestion } from '@/api/evidence-guide.api';
import { AlertTriangle, CheckCircle2, Loader2, Send, Target } from 'lucide-react';

interface Props { caseId: string; }

function getGapTitle(gap: EvidenceGuideGap) {
  return gap.missing_type || gap.type || gap.description || '证据缺口';
}

function GapList({ title, gaps, tone }: { title: string; gaps?: EvidenceGuideGap[]; tone: 'critical' | 'important' | 'optional' }) {
  if (!gaps?.length) return null;
  const badgeVariant = tone === 'critical' ? 'destructive' : tone === 'important' ? 'secondary' : 'outline';
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium">{title}</h3>
        <Badge variant={badgeVariant}>{gaps.length}</Badge>
      </div>
      <div className="grid gap-2">
        {gaps.map((gap, index) => (
          <div key={gap.id || `${title}-${index}`} className="rounded-md border p-3">
            <p className="text-sm font-medium">{getGapTitle(gap)}</p>
            {(gap.suggestion || gap.action) && (
              <p className="mt-1 text-sm text-muted-foreground">{gap.suggestion || gap.action}</p>
            )}
            {gap.description && gap.description !== getGapTitle(gap) && (
              <p className="mt-1 text-xs text-muted-foreground">{gap.description}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function GuidanceQuestion({ question }: { question: EvidenceGuideQuestion }) {
  return (
    <div className="rounded-md border p-3">
      <div className="flex flex-wrap items-center gap-2">
        {question.category && <Badge variant="outline">{question.category}</Badge>}
        <p className="text-sm font-medium">{question.question}</p>
      </div>
      {question.help_text && <p className="mt-1 text-xs text-muted-foreground">{question.help_text}</p>}
      {question.options?.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {question.options.map((option, index) => {
            const label = typeof option === 'string' ? option : option.label || option.value || '选项';
            const value = typeof option === 'string' ? option : option.value || option.label || String(index);
            return <Badge key={`${value}-${index}`} variant="secondary">{label}</Badge>;
          })}
        </div>
      ) : null}
    </div>
  );
}

export function EvidenceGuide({ caseId }: Props) {
  const [answer, setAnswer] = useState('有书面合同和银行转账记录');
  const { data, isLoading, isError } = useEvidenceGuideHook(caseId);
  const answerMutation = useAnswerGuideQuestion();
  const firstQuestion = data?.guidance_questions?.[0] || null;
  const latestAnswer = answerMutation.data;
  const score = Math.round(data?.diagnosis?.overall_score || 0);
  const proofCompleteness = Math.round(data?.diagnosis?.proof_chain_completeness || score || 0);

  if (isLoading) {
    return <div className="h-32 animate-pulse rounded-md bg-muted" />;
  }

  if (isError) {
    return (
      <Card>
        <CardHeader><CardTitle>证据引导</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">证据诊断加载失败，请检查案件和后端服务状态。</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">证据引导</h2>
        <p className="text-sm text-muted-foreground">按案件要件诊断证据缺口，并给出补证问题</p>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">准备度</p>
            <p className="mt-1 text-2xl font-semibold">{score}%</p>
            <p className="text-xs text-muted-foreground">{data?.diagnosis?.readiness_level || '待评估'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">证明链完整性</p>
            <p className="mt-1 text-2xl font-semibold">{proofCompleteness}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">已提交证据</p>
            <p className="mt-1 text-2xl font-semibold">{data?.diagnosis?.evidence_count || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-sm text-muted-foreground">关键缺口</p>
            <p className="mt-1 text-2xl font-semibold">{data?.diagnosis?.critical_gaps_count || 0}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4" />
            证据完整性
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Progress value={proofCompleteness} />
          <div className="mt-2 flex justify-between text-xs text-muted-foreground">
            <span>0%</span>
            <span>{proofCompleteness}%</span>
            <span>100%</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.9fr)]">
        <Card>
          <CardHeader><CardTitle className="text-base">缺口诊断</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            <GapList title="关键缺口" gaps={data?.gaps_analysis?.critical} tone="critical" />
            <GapList title="重要缺口" gaps={data?.gaps_analysis?.important} tone="important" />
            <GapList title="可选补强" gaps={data?.gaps_analysis?.optional} tone="optional" />
            {!data?.gaps_analysis?.critical?.length && !data?.gaps_analysis?.important?.length && !data?.gaps_analysis?.optional?.length && (
              <div className="rounded-md border p-4 text-sm text-muted-foreground">当前未发现明确证据缺口。</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">补证问诊</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {data?.guidance_questions?.length ? (
              data.guidance_questions.slice(0, 3).map((question) => <GuidanceQuestion key={question.id} question={question} />)
            ) : (
              <p className="rounded-md border p-3 text-sm text-muted-foreground">暂无补证问题。</p>
            )}

            {firstQuestion && (
              <div className="space-y-2 pt-2">
                <Textarea
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  placeholder="回答上方第一个补证问题"
                  className="min-h-20"
                />
                <Button
                  onClick={() => answerMutation.mutate({ caseId, questionId: firstQuestion.id, answer })}
                  disabled={answerMutation.isPending || !answer.trim()}
                >
                  {answerMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                  提交引导答案
                </Button>
              </div>
            )}

            {latestAnswer && (
              <div className="rounded-md border bg-muted/20 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <p className="text-sm font-medium">已记录回答</p>
                  {typeof latestAnswer.updated_diagnosis?.score === 'number' && (
                    <Badge variant="secondary">新评分 {Math.round(latestAnswer.updated_diagnosis.score)}%</Badge>
                  )}
                </div>
                {latestAnswer.suggestions?.map((suggestion, index) => (
                  <p key={`${suggestion.message}-${index}`} className="text-sm text-muted-foreground">
                    {suggestion.message}{suggestion.action ? `：${suggestion.action}` : ''}
                  </p>
                ))}
                {latestAnswer.next_question && (
                  <p className="mt-2 text-sm">下一问：{latestAnswer.next_question.question}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
