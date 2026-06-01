import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentCase } from '@/contexts/use-current-case';
import type { Case } from '@/types/case.types';
import { useNavigate } from 'react-router-dom';
import { LinkBadge } from '@/components/common/link-badge';
import { StatusBadge } from '@/components/common/status-badge';
import { UrgencyBadge } from '@/components/common/urgency-badge';

interface CaseCardProps {
  caseData: Case;
  urgency?: 'expired' | 'urgent' | 'warning' | 'normal';
  daysRemaining?: number;
  labels?: {
    plaintiffLabel: string;
    defendantLabel: string;
    evidenceLabel: string;
    documentLabel: string;
    deadlineLabel: string;
    selectPrefix: string;
  };
  selectable?: boolean;
  selected?: boolean;
  onSelect?: (caseId: string, selected: boolean) => void;
}

export function CaseCard({
  caseData,
  urgency = 'normal',
  daysRemaining = 30,
  labels = {
    plaintiffLabel: '原告/申请人',
    defendantLabel: '被告/被执行人',
    evidenceLabel: '证据',
    documentLabel: '文书',
    deadlineLabel: '截止日',
    selectPrefix: '选择案件',
  },
  selectable = false,
  selected = false,
  onSelect,
}: CaseCardProps) {
  const navigate = useNavigate();
  const { setCurrentCaseId } = useCurrentCase();
  const statusMap: Record<Case['status'], 'completed' | 'in-progress' | 'urgent' | 'warning' | 'draft' | 'closed'> = {
    preparing: 'draft',
    negotiating: 'in-progress',
    litigating: 'urgent',
    appealing: 'warning',
    executing: 'in-progress',
    closed: 'closed',
  };

  const handleCardClick = (event: React.MouseEvent) => {
    if ((event.target as HTMLElement).closest('.checkbox-area')) {
      return;
    }

    if (!selectable) {
      setCurrentCaseId(caseData.id);
      navigate(`/cases/${caseData.id}`);
    }
  };

  const handleCheckboxChange = (checked: boolean) => {
    onSelect?.(caseData.id, checked);
  };

  return (
    <Card
      data-testid="case-card"
      className={`cursor-pointer transition-all hover:shadow-md ${
        selected ? 'border-primary ring-2 ring-primary' : ''
      }`}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 flex-1 items-start gap-2">
            {selectable && (
              <div className="checkbox-area mt-1 flex-shrink-0" onClick={(event) => event.stopPropagation()}>
                <Checkbox
                  checked={selected}
                  onCheckedChange={handleCheckboxChange}
                  aria-label={`${labels.selectPrefix} ${caseData.title}`}
                />
              </div>
            )}
            <CardTitle className="truncate text-base">{caseData.title}</CardTitle>
          </div>
          <div className="flex flex-shrink-0 items-center gap-2">
            <StatusBadge label={caseData.status} variant={statusMap[caseData.status]} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {labels.plaintiffLabel}：{caseData.plaintiff?.name || '未记录'} · {labels.defendantLabel}：{caseData.defendant?.name || '未记录'}
        </p>
        <div className="mt-2 flex items-center gap-2">
          <LinkBadge count={caseData.evidenceCount} label={labels.evidenceLabel} />
          <LinkBadge count={caseData.documentCount} label={labels.documentLabel} />
          <LinkBadge count={caseData.deadlineCount} label={labels.deadlineLabel} />
        </div>
        {caseData.amount && (
          <p className="mt-2 text-sm font-medium">¥{caseData.amount.toLocaleString()}</p>
        )}
        <UrgencyBadge daysRemaining={daysRemaining} urgency={urgency} />
      </CardContent>
    </Card>
  );
}
