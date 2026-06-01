import { fireEvent } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { EvidencePanel } from './evidence-panel';

describe('Smart Chat EvidencePanel', () => {
  it('shows manual review workpaper fields for reviewed evidence', () => {
    render(
      <EvidencePanel
        evidenceList={[
          {
            id: 'ev-1',
            display_name: '微信聊天记录导出文件',
            evidence_type: '电子证据',
            summary: '双方确认欠款本金',
            proves_facts: ['对方确认欠款'],
            evidence_review: {
              proof_purpose: '证明对方确认欠款本金',
              original_status: '已核验原始聊天导出文件',
              formed_at: '2026-05-30',
              authenticity_risk: '需保留原始聊天记录',
              legality_risk: '由我方账号依法导出',
              relevance_risk: '与欠款确认直接相关',
              strengthening_actions: ['补充原始聊天导出文件', '核对对方账号主体'],
              review_notes: '提交前核验上下文完整性',
            },
          },
        ]}
      />,
    );

    expect(screen.getByText('已人工复核')).toBeInTheDocument();
    fireEvent.click(screen.getByText('微信聊天记录导出文件'));

    expect(screen.getByText('人工复核工作底稿')).toBeInTheDocument();
    expect(screen.getByText('证明对方确认欠款本金')).toBeInTheDocument();
    expect(screen.getByText('已核验原始聊天导出文件')).toBeInTheDocument();
    expect(screen.getByText('需保留原始聊天记录')).toBeInTheDocument();
    expect(screen.getByText('由我方账号依法导出')).toBeInTheDocument();
    expect(screen.getByText('与欠款确认直接相关')).toBeInTheDocument();
    expect(screen.getByText('补充原始聊天导出文件；核对对方账号主体')).toBeInTheDocument();
    expect(screen.getByText('提交前核验上下文完整性')).toBeInTheDocument();
  });

  it('marks unreviewed evidence as pending manual review', () => {
    render(
      <EvidencePanel
        evidenceList={[
          {
            id: 'ev-2',
            display_name: '付款凭证',
            evidence_type: '书证',
            summary: '付款记录摘要',
          },
        ]}
      />,
    );

    expect(screen.getByText('待人工复核')).toBeInTheDocument();
    fireEvent.click(screen.getByText('付款凭证'));

    expect(screen.getByText('人工复核工作底稿')).toBeInTheDocument();
    expect(screen.getByText('待人工填写')).toBeInTheDocument();
    expect(screen.getAllByText('待核验').length).toBeGreaterThanOrEqual(1);
  });
});
