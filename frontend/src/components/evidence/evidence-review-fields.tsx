import { AlertTriangle, ClipboardCheck, FileText, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

type EvidenceFact = string | { fact?: string };

export interface EvidenceReviewSource {
  id?: string | number;
  display_name?: string;
  original_filename?: string;
  evidence_type?: string;
  summary?: string;
  extracted_content?: string;
  raw_content?: string;
  proves_facts?: EvidenceFact[];
  credibility_score?: number | null;
  status?: string;
  source_party?: string;
  created_at?: string;
}

interface EvidenceReviewFieldsProps {
  evidence: EvidenceReviewSource;
}

interface ReviewField {
  label: string;
  value: string;
  status: 'ok' | 'warning' | 'pending';
}

const ELECTRONIC_EXTENSIONS = new Set([
  'jpg',
  'jpeg',
  'png',
  'gif',
  'bmp',
  'webp',
  'tiff',
  'pdf',
  'eml',
  'msg',
  'html',
  'htm',
  'xlsx',
  'xls',
  'csv',
  'docx',
  'doc',
  'txt',
]);

const SOURCE_LABELS: Record<string, string> = {
  OUR_SIDE: '我方提供',
  OPPONENT: '对方提供',
  THIRD_PARTY: '第三方材料',
  COURT: '法院/仲裁机构材料',
  own: '我方提供',
  opponent: '对方提供',
  third_party: '第三方材料',
};

function normalizeFact(fact: EvidenceFact): string {
  if (typeof fact === 'string') return fact;
  return fact.fact || JSON.stringify(fact);
}

function formatDate(value?: string) {
  if (!value) return '待人工补录形成时间或取得时间';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('zh-CN');
}

function getFileExtension(filename?: string) {
  return filename?.split('.').pop()?.toLowerCase() || '';
}

function inferOriginalStatus(evidence: EvidenceReviewSource) {
  const filename = evidence.original_filename || evidence.display_name || '';
  const ext = getFileExtension(filename);
  const typeText = `${evidence.evidence_type || ''} ${filename}`.toLowerCase();

  if (typeText.includes('截图') || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)) {
    return '截图/影像材料，需核验原始载体';
  }
  if (['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'eml', 'msg'].includes(ext)) {
    return '电子文件，需核验原始文件和导出路径';
  }
  return '原件/复印件状态待人工标注';
}

function isLikelyElectronicEvidence(evidence: EvidenceReviewSource) {
  const filename = evidence.original_filename || evidence.display_name || '';
  const ext = getFileExtension(filename);
  const typeText = `${evidence.evidence_type || ''} ${evidence.summary || ''} ${filename}`.toLowerCase();
  return (
    ELECTRONIC_EXTENSIONS.has(ext) ||
    ['微信', '聊天', '邮件', '截图', '电子', '转账', '流水'].some((keyword) => typeText.includes(keyword.toLowerCase()))
  );
}

function riskFromScore(score?: number | null) {
  if (score == null) return '待核验';
  if (score >= 80) return '较低';
  if (score >= 60) return '中等';
  return '较高';
}

export function buildEvidenceReviewFields(evidence: EvidenceReviewSource): ReviewField[] {
  const facts = evidence.proves_facts?.map(normalizeFact).filter(Boolean) || [];
  const source = evidence.source_party ? SOURCE_LABELS[evidence.source_party] || evidence.source_party : '来源方待核验';
  const content = evidence.extracted_content || evidence.raw_content || evidence.summary || '';
  const proofPurpose = facts.length > 0
    ? facts.slice(0, 2).join('；')
    : evidence.summary || '证明目的待人工补录';
  const authenticityRisk = riskFromScore(evidence.credibility_score);

  return [
    { label: '材料来源', value: source, status: evidence.source_party ? 'ok' : 'pending' },
    { label: '形成/取得时间', value: formatDate(evidence.created_at), status: evidence.created_at ? 'ok' : 'pending' },
    { label: '原件状态', value: inferOriginalStatus(evidence), status: 'warning' },
    { label: '证明目的', value: proofPurpose, status: facts.length > 0 || evidence.summary ? 'ok' : 'pending' },
    { label: '真实性风险', value: authenticityRisk, status: authenticityRisk === '较高' ? 'warning' : authenticityRisk === '待核验' ? 'pending' : 'ok' },
    { label: '合法性风险', value: '需核验取得方式、授权范围和是否涉及隐私/商业秘密', status: 'warning' },
    { label: '关联性风险', value: facts.length > 0 ? '已有关联事实，仍需确认与诉请/抗辩的对应关系' : '缺少关联事实标注', status: facts.length > 0 ? 'ok' : 'pending' },
    { label: '内容可读性', value: content.trim() ? '已提取正文或摘要，可继续复核' : '未提取到正文，需补充扫描、OCR 或原件', status: content.trim() ? 'ok' : 'warning' },
  ];
}

export function EvidenceReviewFields({ evidence }: EvidenceReviewFieldsProps) {
  const fields = buildEvidenceReviewFields(evidence);
  const facts = evidence.proves_facts?.map(normalizeFact).filter(Boolean) || [];
  const electronic = isLikelyElectronicEvidence(evidence);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <ClipboardCheck className="h-4 w-4 text-primary" />
          证据固定审查字段
          <Badge variant="outline">待人工复核</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          {fields.map((field) => (
            <div key={field.label} className="rounded-md border p-3">
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-xs font-medium text-muted-foreground">{field.label}</p>
                <StatusDot status={field.status} />
              </div>
              <p className="text-sm leading-6">{field.value}</p>
            </div>
          ))}
        </div>

        {facts.length > 0 && (
          <div className="rounded-md border p-3">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <FileText className="h-4 w-4 text-muted-foreground" />
              关联事实
            </div>
            <ul className="space-y-1 pl-4 text-sm text-muted-foreground">
              {facts.slice(0, 5).map((fact, index) => (
                <li key={`${fact}-${index}`} className="list-disc">{fact}</li>
              ))}
            </ul>
          </div>
        )}

        {electronic && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
            <div className="mb-1 flex items-center gap-2 font-medium">
              <AlertTriangle className="h-4 w-4" />
              电子证据核验提示
            </div>
            <p className="leading-6">
              请补充或核验原始载体、导出方式、账号主体、时间戳、上下文完整性和必要的存证/公证记录。
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StatusDot({ status }: { status: ReviewField['status'] }) {
  if (status === 'ok') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-700 dark:text-emerald-300">
        <ShieldCheck className="h-3.5 w-3.5" />
        已有依据
      </span>
    );
  }
  if (status === 'warning') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-amber-700 dark:text-amber-300">
        <AlertTriangle className="h-3.5 w-3.5" />
        需核验
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-slate-500">
      <AlertTriangle className="h-3.5 w-3.5" />
      待补录
    </span>
  );
}
