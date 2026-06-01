import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import {
  EvidenceReviewFields,
  buildEvidenceReviewFields,
  type EvidenceReviewSource,
} from '@/components/evidence/evidence-review-fields';

const baseEvidence: EvidenceReviewSource = {
  id: 'ev-1',
  display_name: '微信聊天记录截图',
  original_filename: 'chat.png',
  evidence_type: '电子证据',
  summary: '双方确认欠款金额',
  extracted_content: '甲方确认尚欠乙方 10 万元。',
  proves_facts: ['对方确认欠款金额', { fact: '欠款发生于合作期间' }],
  credibility_score: 72,
  status: 'processed',
  source_party: 'OUR_SIDE',
  created_at: '2026-05-30T08:00:00Z',
};

describe('EvidenceReviewFields', () => {
  it('renders fixed review fields for evidence details', () => {
    render(<EvidenceReviewFields evidence={baseEvidence} />);

    expect(screen.getByText('证据固定审查字段')).toBeInTheDocument();
    expect(screen.getByText('材料来源')).toBeInTheDocument();
    expect(screen.getByText('我方提供')).toBeInTheDocument();
    expect(screen.getByText('证明目的')).toBeInTheDocument();
    expect(screen.getAllByText(/对方确认欠款金额/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('真实性风险')).toBeInTheDocument();
    expect(screen.getByText('中等')).toBeInTheDocument();
  });

  it('shows electronic evidence verification reminder', () => {
    render(<EvidenceReviewFields evidence={baseEvidence} />);

    expect(screen.getByText('电子证据核验提示')).toBeInTheDocument();
    expect(screen.getByText(/原始载体、导出方式、账号主体、时间戳/)).toBeInTheDocument();
  });

  it('marks missing proof purpose and source as pending', () => {
    const fields = buildEvidenceReviewFields({
      id: 'ev-2',
      display_name: '空白材料',
      original_filename: 'note.unknown',
      evidence_type: '',
      proves_facts: [],
      credibility_score: null,
    });

    expect(fields.find((field) => field.label === '材料来源')).toMatchObject({
      value: '来源方待核验',
      status: 'pending',
    });
    expect(fields.find((field) => field.label === '证明目的')).toMatchObject({
      value: '证明目的待人工补录',
      status: 'pending',
    });
    expect(fields.find((field) => field.label === '内容可读性')).toMatchObject({
      status: 'warning',
    });
  });
});
