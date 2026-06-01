import { describe, expect, it } from 'vitest';
import { buildEvidenceWorkpaperExportText } from './evidence-export-workpaper';

describe('buildEvidenceWorkpaperExportText', () => {
  it('includes manual review fields in single evidence exports', () => {
    const text = buildEvidenceWorkpaperExportText({
      display_name: '微信聊天记录导出文件',
      evidence_type: '电子证据',
      source_party: '我方',
      credibility_score: 72,
      created_at: '2026-06-01T08:00:00Z',
      summary: '双方确认欠款本金',
      extracted_content: '对方确认尚欠本金。',
      proves_facts: [{ fact: '对方确认欠款' }],
      evidence_review: {
        review_status: 'reviewed',
        reviewed_by: 'pytest-user',
        reviewed_at: '2026-06-01T09:00:00Z',
        source: '我方账号导出',
        formed_at: '2026-05-30',
        original_status: '已核验原始聊天导出文件',
        proof_purpose: '证明对方确认欠款本金',
        authenticity_risk: '需保留原始聊天记录',
        legality_risk: '由我方账号依法导出',
        relevance_risk: '与欠款确认直接相关',
        strengthening_actions: ['补充原始聊天导出文件', '核对对方账号主体'],
        review_notes: '提交前核验上下文完整性',
      },
    });

    expect(text).toContain('【人工复核工作底稿】');
    expect(text).toContain('复核状态：已人工复核');
    expect(text).toContain('材料来源：我方账号导出');
    expect(text).toContain('原件状态：已核验原始聊天导出文件');
    expect(text).toContain('证明目的：证明对方确认欠款本金');
    expect(text).toContain('真实性风险：需保留原始聊天记录');
    expect(text).toContain('合法性风险：由我方账号依法导出');
    expect(text).toContain('关联性风险：与欠款确认直接相关');
    expect(text).toContain('补强动作：补充原始聊天导出文件；核对对方账号主体');
    expect(text).toContain('复核备注：提交前核验上下文完整性');
    expect(text).toContain('1. 对方确认欠款');
    expect(text).toContain('对方确认尚欠本金。');
  });

  it('marks missing review fields as pending workpaper items', () => {
    const text = buildEvidenceWorkpaperExportText({
      original_filename: 'receipt.pdf',
      evidence_type: '书证',
      summary: '付款记录摘要',
      evidence_review: null,
    });

    expect(text).toContain('复核状态：待人工复核');
    expect(text).toContain('原件状态：待核验');
    expect(text).toContain('证明目的：待人工填写');
    expect(text).toContain('真实性风险：待人工核验');
    expect(text).toContain('补强动作：暂无补强动作，提交前仍需核验原件和上下文');
  });
});
