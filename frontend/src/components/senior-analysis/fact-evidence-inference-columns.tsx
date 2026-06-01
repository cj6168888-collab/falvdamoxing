import { AlertTriangle, Brain, FileCheck2 } from 'lucide-react';
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

  return {
    establishedFacts: unique(establishedFacts),
    aiInferences: unique(aiInferences),
    unverifiedItems: unique(unverifiedItems),
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
  icon: typeof FileCheck2;
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
