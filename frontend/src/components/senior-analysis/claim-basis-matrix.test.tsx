import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ClaimBasisMatrix, buildClaimBasisRows } from '@/components/senior-analysis/claim-basis-matrix';

const requirementsCheck = {
  requirements: [
    {
      requirement: '合同违约责任',
      elements: ['合同成立', '违约行为', '损失事实'],
      evidence_required: ['合同文本', '付款记录'],
      common_issues: ['合同主体混同', '损失金额计算不清'],
      status: 'partial',
      covered_elements: [
        {
          element: '合同成立',
          evidence: [{ evidence_id: 'ev-1', type: '合同', credibility: 88 }],
        },
      ],
      missing_elements: ['违约行为', '损失事实'],
    },
  ],
};

describe('ClaimBasisMatrix', () => {
  it('builds claim basis rows from requirements check output', () => {
    const rows = buildClaimBasisRows(requirementsCheck);

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      claim_basis: '合同违约责任',
      risk_level: 'medium',
      requires_human_review: true,
    });
    expect(rows[0].supporting_evidence).toContain('ev-1/合同/信度88');
    expect(rows[0].missing_evidence).toEqual(['违约行为', '损失事实']);
  });

  it('renders a visible matrix with evidence anchors and gaps', () => {
    render(<ClaimBasisMatrix requirementsCheck={requirementsCheck} />);

    expect(screen.getByText('请求权基础矩阵')).toBeInTheDocument();
    expect(screen.getByText('工作底稿')).toBeInTheDocument();
    expect(screen.getByText('合同违约责任')).toBeInTheDocument();
    expect(screen.getByText('部分要件待补强')).toBeInTheDocument();
    expect(screen.getByText('中风险')).toBeInTheDocument();
    expect(screen.getByText('ev-1/合同/信度88')).toBeInTheDocument();
    expect(screen.getAllByText('违约行为').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('损失金额计算不清')).toBeInTheDocument();
  });

  it('does not render when there are no requirements', () => {
    const { container } = render(<ClaimBasisMatrix requirementsCheck={{ requirements: [] }} />);

    expect(container).toBeEmptyDOMElement();
  });
});
