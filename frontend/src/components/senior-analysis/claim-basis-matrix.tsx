import { AlertTriangle, CheckCircle2, ClipboardList } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface EvidenceCoverage {
  element?: string;
  evidence?: Array<{
    evidence_id?: string | number;
    type?: string;
    credibility?: number | null;
  }>;
}

interface RequirementCheck {
  requirement?: string;
  elements?: string[];
  evidence_required?: string[];
  common_issues?: string[];
  status?: string;
  covered_elements?: EvidenceCoverage[];
  missing_elements?: string[];
  gaps?: string[];
  suggestions?: string[];
}

interface RequirementsCheck {
  requirements?: RequirementCheck[];
}

export interface ClaimBasisRow {
  claim_basis: string;
  legal_elements: string[];
  facts_to_prove: string[];
  supporting_evidence: string[];
  missing_evidence: string[];
  opponent_defenses: string[];
  risk_level: 'high' | 'medium' | 'low';
  requires_human_review: true;
}

interface ClaimBasisMatrixProps {
  requirementsCheck?: RequirementsCheck | null;
}

const STATUS_LABELS: Record<string, string> = {
  complete: '要件覆盖较完整',
  partial: '部分要件待补强',
  incomplete: '核心要件缺口',
  pending: '待人工核验',
};

function riskFromStatus(status?: string): ClaimBasisRow['risk_level'] {
  if (status === 'complete') return 'low';
  if (status === 'partial') return 'medium';
  return 'high';
}

function riskLabel(risk: ClaimBasisRow['risk_level']) {
  return { low: '低风险', medium: '中风险', high: '高风险' }[risk];
}

function riskVariant(risk: ClaimBasisRow['risk_level']): 'default' | 'secondary' | 'destructive' {
  if (risk === 'low') return 'default';
  if (risk === 'medium') return 'secondary';
  return 'destructive';
}

export function buildClaimBasisRows(requirementsCheck?: RequirementsCheck | null): ClaimBasisRow[] {
  return (requirementsCheck?.requirements || []).map((item) => {
    const covered = item.covered_elements || [];
    const supportingEvidence = covered.flatMap((coverage) =>
      (coverage.evidence || []).map((evidence) => {
        const id = evidence.evidence_id ?? '未编号证据';
        const type = evidence.type ? `/${evidence.type}` : '';
        const credibility = typeof evidence.credibility === 'number' ? `/信度${evidence.credibility}` : '';
        return `${id}${type}${credibility}`;
      }),
    );
    const coveredFacts = covered.map((coverage) => coverage.element).filter(Boolean) as string[];

    return {
      claim_basis: item.requirement || '待识别请求权基础',
      legal_elements: item.elements || [],
      facts_to_prove: [...coveredFacts, ...(item.missing_elements || [])],
      supporting_evidence: supportingEvidence,
      missing_evidence: item.missing_elements || [],
      opponent_defenses: item.common_issues || item.gaps || [],
      risk_level: riskFromStatus(item.status),
      requires_human_review: true,
    };
  });
}

export function ClaimBasisMatrix({ requirementsCheck }: ClaimBasisMatrixProps) {
  const rows = buildClaimBasisRows(requirementsCheck);

  if (rows.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ClipboardList className="h-4 w-4 text-primary" />
          请求权基础矩阵
          <Badge variant="outline">工作底稿</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {rows.map((row) => (
          <div key={row.claim_basis} className="rounded-md border p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h4 className="font-medium">{row.claim_basis}</h4>
                <p className="mt-1 text-xs text-muted-foreground">
                  {STATUS_LABELS[requirementsCheck?.requirements?.find((item) => item.requirement === row.claim_basis)?.status || 'pending'] || '待人工核验'}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant={riskVariant(row.risk_level)}>{riskLabel(row.risk_level)}</Badge>
                <Badge variant="outline">需人工复核</Badge>
              </div>
            </div>

            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              <MatrixBlock title="构成要件" items={row.legal_elements} emptyText="暂无要件" />
              <MatrixBlock title="事实/证明对象" items={row.facts_to_prove} emptyText="待补事实" />
              <MatrixBlock title="支持证据" items={row.supporting_evidence} emptyText="暂无已锚定证据" />
              <MatrixBlock title="缺口证据" items={row.missing_evidence} emptyText="暂无缺口" warning={row.missing_evidence.length > 0} />
              <MatrixBlock title="对方可能抗辩/常见问题" items={row.opponent_defenses} emptyText="待补充抗辩点" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function MatrixBlock({
  title,
  items,
  emptyText,
  warning = false,
}: {
  title: string;
  items: string[];
  emptyText: string;
  warning?: boolean;
}) {
  const Icon = warning ? AlertTriangle : CheckCircle2;
  return (
    <div className="rounded-md bg-muted/30 p-3">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {title}
      </div>
      {items.length > 0 ? (
        <ul className="space-y-1 pl-4 text-sm">
          {items.map((item, index) => (
            <li key={`${title}-${item}-${index}`} className="list-disc leading-6">{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">{emptyText}</p>
      )}
    </div>
  );
}
