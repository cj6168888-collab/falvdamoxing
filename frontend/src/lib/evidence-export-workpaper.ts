type EvidenceFact = string | { fact?: string };

export interface EvidenceExportReview {
  review_status?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  source?: string | null;
  formed_at?: string | null;
  original_status?: string | null;
  proof_purpose?: string | null;
  authenticity_risk?: string | null;
  legality_risk?: string | null;
  relevance_risk?: string | null;
  strengthening_actions?: string[];
  review_notes?: string | null;
}

export interface EvidenceExportSource {
  display_name?: string | null;
  original_filename?: string | null;
  evidence_type?: string | null;
  summary?: string | null;
  extracted_content?: string | null;
  raw_content?: string | null;
  proves_facts?: EvidenceFact[];
  credibility_score?: number | null;
  source_party?: string | null;
  created_at?: string | null;
  evidence_review?: EvidenceExportReview | null;
}

function formatDateTime(value?: string | null) {
  if (!value) return '待核验';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN');
}

function normalizeFact(fact: EvidenceFact) {
  if (typeof fact === 'string') return fact;
  return fact.fact || JSON.stringify(fact);
}

function formatActions(actions?: string[]) {
  if (!actions || actions.length === 0) return '暂无补强动作，提交前仍需核验原件和上下文';
  return actions.filter(Boolean).join('；') || '暂无补强动作，提交前仍需核验原件和上下文';
}

export function buildEvidenceWorkpaperExportText(evidence: EvidenceExportSource) {
  const review = evidence.evidence_review;
  const name = evidence.display_name || evidence.original_filename || '未命名证据';
  const content = evidence.extracted_content || evidence.raw_content || evidence.summary || '无内容';
  const facts = (evidence.proves_facts || []).map(normalizeFact).filter(Boolean);

  return [
    `证据名称：${name}`,
    `证据类型：${evidence.evidence_type || '未分类'}`,
    `来源方：${evidence.source_party || '未知'}`,
    `证明力参考：${evidence.credibility_score ?? '未评估'}（仅作工作底稿参考，不等同于法院采信结论）`,
    `创建时间：${formatDateTime(evidence.created_at)}`,
    '',
    '【人工复核工作底稿】',
    `复核状态：${review?.review_status === 'reviewed' ? '已人工复核' : '待人工复核'}`,
    `复核人：${review?.reviewed_by || '未记录'}`,
    `复核时间：${formatDateTime(review?.reviewed_at)}`,
    `材料来源：${review?.source || evidence.source_party || '待核验'}`,
    `形成/取得时间：${review?.formed_at || '待核验'}`,
    `原件状态：${review?.original_status || '待核验'}`,
    `证明目的：${review?.proof_purpose || '待人工填写'}`,
    `真实性风险：${review?.authenticity_risk || '待人工核验'}`,
    `合法性风险：${review?.legality_risk || '待人工核验'}`,
    `关联性风险：${review?.relevance_risk || '待人工核验'}`,
    `补强动作：${formatActions(review?.strengthening_actions)}`,
    `复核备注：${review?.review_notes || '无'}`,
    '',
    '【证明事实】',
    facts.length > 0 ? facts.map((fact, index) => `${index + 1}. ${fact}`).join('\n') : '待人工补录证明事实',
    '',
    '【证据内容】',
    content,
  ].join('\n');
}
