import { AlertTriangle, Brain, CheckSquare, FileCheck2 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface EvidenceAnchor {
  evidence_id?: string | number;
  type?: string;
  credibility?: number | null;
}

interface EvidenceInventory {
  evidence_mapping?: Record<string, EvidenceAnchor[]>;
}

interface CaseUnderstanding {
  core_disputes?: string[];
  uncertain_aspects?: string[];
}

interface RequirementCheck {
  requirement?: string;
  status?: string;
  missing_elements?: string[];
  suggestions?: string[];
}

interface RequirementsCheck {
  requirements?: RequirementCheck[];
  total_gaps?: Array<{ requirement?: string; element?: string }>;
}

interface Issues {
  evidence_gaps?: Array<{
    fact?: string;
    requirement?: string;
    suggestion?: string;
    obtain_method?: string;
  }>;
  procedure_issues?: Array<{
    issue?: string;
    suggestion?: string;
  }>;
  weak_arguments?: Array<{
    issue?: string;
    weakness?: string;
    strengthening?: string;
  }>;
  risk_points?: Array<{
    point?: string;
    mitigation?: string;
  }>;
}

interface Props {
  caseUnderstanding?: CaseUnderstanding | null;
  evidenceInventory?: EvidenceInventory | null;
  requirementsCheck?: RequirementsCheck | null;
  issues?: Issues | null;
  recommendations?: unknown;
}

export interface FactInferenceColumnsData {
  establishedFacts: string[];
  aiInferences: string[];
  unverifiedItems: string[];
  reviewTasks: ReviewTask[];
}

export interface ReviewTask {
  title: string;
  category: '补证' | '程序核验' | '事实核验' | '论证补强';
  nextAction: string;
  priority: 'high' | 'medium';
}

function evidenceLabel(anchor: EvidenceAnchor) {
  const id = anchor.evidence_id ?? '未编号证据';
  const type = anchor.type ? `/${anchor.type}` : '';
  const credibility = typeof anchor.credibility === 'number' ? `/信度${anchor.credibility}` : '';
  return `${id}${type}${credibility}`;
}

function collectRecommendationText(value: unknown): string[] {
  if (!value) return [];
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(collectRecommendationText);
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .filter(([key]) => ['action', 'recommendation', 'suggestion', 'title', 'description'].includes(key))
      .flatMap(([, item]) => collectRecommendationText(item));
  }
  return [];
}

function unique(items: string[]) {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean)));
}

function uniqueTasks(tasks: ReviewTask[]) {
  const seen = new Set<string>();
  return tasks.filter((task) => {
    const key = `${task.category}:${task.title}:${task.nextAction}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function buildFactInferenceColumns({
  caseUnderstanding,
  evidenceInventory,
  requirementsCheck,
  issues,
  recommendations,
}: Props): FactInferenceColumnsData {
  const establishedFacts = Object.entries(evidenceInventory?.evidence_mapping || {}).map(([fact, anchors]) => {
    const anchorText = (anchors || []).map(evidenceLabel).join('、');
    return `${fact}（证据：${anchorText || '待补证据编号'}）`;
  });

  const requirementInferences = (requirementsCheck?.requirements || []).map((item) => {
    const status = item.status === 'complete'
      ? '要件覆盖较完整'
      : item.status === 'partial'
        ? '部分要件待补强'
        : '要件缺口较高';
    return `${item.requirement || '待识别请求权基础'}：${status}`;
  });

  const aiInferences = [
    ...(caseUnderstanding?.core_disputes || []).map((item) => `争议焦点推断：${item}`),
    ...requirementInferences,
    ...collectRecommendationText(recommendations).slice(0, 5).map((item) => `下一步建议：${item}`),
  ];

  const requirementGaps = (requirementsCheck?.total_gaps || []).map((gap) =>
    `${gap.requirement || '待识别请求权基础'}缺少${gap.element || '证明要件'}`,
  );
  const evidenceGaps = (issues?.evidence_gaps || []).map((gap) =>
    `${gap.requirement || '待识别要件'}：${gap.fact || gap.suggestion || '证据缺口待核验'}`,
  );
  const procedureIssues = (issues?.procedure_issues || []).map((item) =>
    `${item.issue || '程序事项待核验'}${item.suggestion ? `；${item.suggestion}` : ''}`,
  );
  const weakArguments = (issues?.weak_arguments || []).map((item) =>
    `${item.issue || item.weakness || '论证薄弱点待核验'}${item.strengthening ? `；${item.strengthening}` : ''}`,
  );

  const unverifiedItems = [
    ...(caseUnderstanding?.uncertain_aspects || []),
    ...requirementGaps,
    ...evidenceGaps,
    ...procedureIssues,
    ...weakArguments,
  ];
  const reviewTasks: ReviewTask[] = [
    ...(caseUnderstanding?.uncertain_aspects || []).map((item) => ({
      title: item,
      category: '事实核验' as const,
      nextAction: '补录或核对案件基础信息，并标注信息来源。',
      priority: 'medium' as const,
    })),
    ...(requirementsCheck?.total_gaps || []).map((gap) => ({
      title: `${gap.requirement || '待识别请求权基础'}缺少${gap.element || '证明要件'}`,
      category: '补证' as const,
      nextAction: `收集或关联能够证明“${gap.element || '该要件'}”的证据，并补充证明目的。`,
      priority: 'high' as const,
    })),
    ...(issues?.evidence_gaps || []).map((gap) => ({
      title: `${gap.requirement || '待识别要件'}：${gap.fact || gap.suggestion || '证据缺口待核验'}`,
      category: '补证' as const,
      nextAction: gap.obtain_method || gap.suggestion || '补充直接证据、原件或可相互印证的辅助材料。',
      priority: 'high' as const,
    })),
    ...(issues?.procedure_issues || []).map((item) => ({
      title: item.issue || '程序事项待核验',
      category: '程序核验' as const,
      nextAction: item.suggestion || '核对管辖、时效、送达、授权或期限等程序事项。',
      priority: 'high' as const,
    })),
    ...(issues?.weak_arguments || []).map((item) => ({
      title: item.issue || item.weakness || '论证薄弱点待核验',
      category: '论证补强' as const,
      nextAction: item.strengthening || '补充证据链、请求权基础或金额计算依据。',
      priority: 'medium' as const,
    })),
  ];

  return {
    establishedFacts: unique(establishedFacts),
    aiInferences: unique(aiInferences),
    unverifiedItems: unique(unverifiedItems),
    reviewTasks: uniqueTasks(reviewTasks),
  };
}

export function FactEvidenceInferenceColumns(props: Props) {
  const data = buildFactInferenceColumns(props);

  if (
    data.establishedFacts.length === 0 &&
    data.aiInferences.length === 0 &&
    data.unverifiedItems.length === 0
  ) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileCheck2 className="h-4 w-4 text-primary" />
          事实-证据-结论三栏
          <Badge variant="outline">待核验工作底稿</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 lg:grid-cols-3">
        <Column
          icon={FileCheck2}
          title="已有事实"
          description="仅列入已绑定证据编号的事实。"
          items={data.establishedFacts}
          emptyText="暂无带证据编号的事实。"
        />
        <Column
          icon={Brain}
          title="AI 推断"
          description="根据事实、要件覆盖和风险项形成的分析。"
          items={data.aiInferences}
          emptyText="暂无可展示推断。"
        />
        <Column
          icon={AlertTriangle}
          title="待核验事项"
          description="可转为补证、核法条或人工确认任务。"
          items={data.unverifiedItems}
          emptyText="暂无待核验事项。"
          warning
        />
      </CardContent>
      {data.reviewTasks.length > 0 && (
        <CardContent className="border-t pt-4">
          <div className="mb-3 flex items-center gap-2 font-medium">
            <CheckSquare className="h-4 w-4 text-primary" />
            待核验任务清单
            <Badge variant="secondary">{data.reviewTasks.length} 项</Badge>
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            {data.reviewTasks.map((task, index) => (
              <div key={`${task.category}-${task.title}-${index}`} className="rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={task.priority === 'high' ? 'destructive' : 'outline'}>
                    {task.priority === 'high' ? '优先核验' : '常规核验'}
                  </Badge>
                  <Badge variant="secondary">{task.category}</Badge>
                </div>
                <p className="mt-2 font-medium leading-6">{task.title}</p>
                <p className="mt-1 text-muted-foreground leading-6">下一步：{task.nextAction}</p>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function Column({
  icon: Icon,
  title,
  description,
  items,
  emptyText,
  warning = false,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  items: string[];
  emptyText: string;
  warning?: boolean;
}) {
  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center gap-2 font-medium">
        <Icon className={warning ? 'h-4 w-4 text-amber-600' : 'h-4 w-4 text-primary'} />
        {title}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      {items.length > 0 ? (
        <ul className="mt-3 space-y-2 pl-4 text-sm">
          {items.map((item, index) => (
            <li key={`${title}-${index}`} className="list-disc leading-6">{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">{emptyText}</p>
      )}
    </div>
  );
}
