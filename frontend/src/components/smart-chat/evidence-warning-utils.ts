import type { EvidenceGap } from './evidence-warning';

// 从风险评估中提取证据缺口
export function extractEvidenceGaps(riskAssessment?: {
  evidence_gaps?: string[];
  key_risks?: string[];
}): EvidenceGap[] {
  if (!riskAssessment?.evidence_gaps?.length) {
    return [];
  }

  return riskAssessment.evidence_gaps.map(gap => {
    const typeMatch = gap.match(/^(合同|借条|转账记录|聊天记录|证人证言|鉴定意见|发票|收据|邮件|函件)/);
    const type = typeMatch ? typeMatch[1] : '其他证据';

    const importanceMatch = gap.match(/(关键|重要|必要|一般)/);
    const importance = importanceMatch ? `${importanceMatch[1]}证据` : '建议补充';

    return {
      type,
      description: gap,
      importance,
    };
  });
}
