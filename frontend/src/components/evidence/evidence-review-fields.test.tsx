import { fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { saveEvidenceFixedReview } from '@/api/evidence.api';
import {
  EvidenceReviewFields,
  buildEvidenceReviewFields,
  type EvidenceReviewSource,
} from '@/components/evidence/evidence-review-fields';

vi.mock('@/api/evidence.api', () => ({
  saveEvidenceFixedReview: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockSaveEvidenceFixedReview = vi.mocked(saveEvidenceFixedReview);

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
    expect(screen.getAllByText('中等').length).toBeGreaterThanOrEqual(1);
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

  it('saves manual review fields and returns updated evidence', async () => {
    const onSaved = vi.fn();
    mockSaveEvidenceFixedReview.mockResolvedValueOnce({
      success: true,
      evidence: {
        ...baseEvidence,
        evidence_review: {
          review_status: 'reviewed',
          proof_purpose: '证明对方确认欠款本金',
        },
      },
    });

    render(<EvidenceReviewFields evidence={baseEvidence} onSaved={onSaved} />);

    fireEvent.change(screen.getByPlaceholderText('证明目的（必填）'), {
      target: { value: '证明对方确认欠款本金' },
    });
    fireEvent.change(screen.getByPlaceholderText('补强动作，每行一项'), {
      target: { value: '补充原始聊天记录\n核对对方账号主体' },
    });
    fireEvent.click(screen.getByRole('button', { name: '保存人工复核' }));

    await waitFor(() => {
      expect(mockSaveEvidenceFixedReview).toHaveBeenCalledWith('ev-1', expect.objectContaining({
        proof_purpose: '证明对方确认欠款本金',
        strengthening_actions: ['补充原始聊天记录', '核对对方账号主体'],
      }));
    });
    expect(onSaved).toHaveBeenCalledTimes(1);
  });
});
