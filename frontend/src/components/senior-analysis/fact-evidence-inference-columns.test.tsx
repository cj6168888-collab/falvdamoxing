import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import {
  FactEvidenceInferenceColumns,
  buildFactInferenceColumns,
} from '@/components/senior-analysis/fact-evidence-inference-columns';

const analysisData = {
  caseUnderstanding: {
    key_facts: ['未锚定的案件描述不应进入已有事实'],
    core_disputes: ['是否存在违约行为'],
    uncertain_aspects: ['被告主体信息缺失'],
  },
  evidenceInventory: {
    evidence_mapping: {
      合同签署事实: [{ evidence_id: 'ev-1', type: '合同', credibility: 90 }],
      付款事实: [{ evidence_id: 'ev-2', type: '转账记录', credibility: 82 }],
    },
  },
  requirementsCheck: {
    requirements: [
      { requirement: '合同违约责任', status: 'partial' },
    ],
    total_gaps: [
      { requirement: '合同违约责任', element: '违约行为' },
    ],
  },
  issues: {
    evidence_gaps: [
      { requirement: '损失事实', fact: '损失金额计算依据不足' },
    ],
    procedure_issues: [
      { issue: '管辖法院待确认', suggestion: '核对合同管辖条款' },
    ],
  },
  recommendations: [
    { action: '补充付款流水原件' },
  ],
};

describe('FactEvidenceInferenceColumns', () => {
  it('separates evidence anchored facts from AI inferences and unverified items', () => {
    const columns = buildFactInferenceColumns(analysisData);

    expect(columns.establishedFacts).toEqual([
      '合同签署事实（证据：ev-1/合同/信度90）',
      '付款事实（证据：ev-2/转账记录/信度82）',
    ]);
    expect(columns.establishedFacts.join('\n')).not.toContain('未锚定的案件描述');
    expect(columns.aiInferences).toContain('争议焦点推断：是否存在违约行为');
    expect(columns.aiInferences).toContain('合同违约责任：部分要件待补强');
    expect(columns.unverifiedItems).toContain('被告主体信息缺失');
    expect(columns.unverifiedItems).toContain('合同违约责任缺少违约行为');
    expect(columns.reviewTasks).toEqual(expect.arrayContaining([
      expect.objectContaining({
        title: '合同违约责任缺少违约行为',
        category: '补证',
        priority: 'high',
      }),
      expect.objectContaining({
        title: '管辖法院待确认',
        category: '程序核验',
        nextAction: '核对合同管辖条款',
      }),
    ]));
  });

  it('renders the three review columns', () => {
    render(<FactEvidenceInferenceColumns {...analysisData} />);

    expect(screen.getByText('事实-证据-结论三栏')).toBeInTheDocument();
    expect(screen.getByText('已有事实')).toBeInTheDocument();
    expect(screen.getByText('AI 推断')).toBeInTheDocument();
    expect(screen.getByText('待核验事项')).toBeInTheDocument();
    expect(screen.getByText('合同签署事实（证据：ev-1/合同/信度90）')).toBeInTheDocument();
    expect(screen.getByText('下一步建议：补充付款流水原件')).toBeInTheDocument();
    expect(screen.getByText('管辖法院待确认；核对合同管辖条款')).toBeInTheDocument();
    expect(screen.getByText('待核验任务清单')).toBeInTheDocument();
    expect(screen.getAllByText('补证').length).toBeGreaterThan(0);
    expect(screen.getByText('程序核验')).toBeInTheDocument();
    expect(screen.getByText(/下一步：收集或关联能够证明/)).toBeInTheDocument();
  });

  it('does not render when there is no usable content', () => {
    const { container } = render(<FactEvidenceInferenceColumns />);

    expect(container).toBeEmptyDOMElement();
  });
});
