import axiosInstance from '@/api/client';

export interface InsightQuestionResponse {
  needs_clarification: boolean;
  intent?: string;
  key_entities?: string[];
  clarifying_questions?: Array<string | { question?: string; options?: string[] }>;
  answer?: string;
}

export interface InsightReportResponse {
  case_id: number;
  report_type: string;
  content: string;
  segments: Array<{ progress: number; status: string }>;
  generated_at: string;
  word_count: number;
}

export interface InsightReportStatus {
  status: string;
  progress: number;
  segments: Array<Record<string, unknown>>;
  error?: string | null;
}

export interface EvidenceGraphNode {
  id: string;
  name: string;
  type: string;
  credibility?: number;
  credibility_factors?: string[];
  proves_facts?: string[];
  related_evidence?: string[];
  contradicts_evidence?: string[];
  keywords?: string[];
}

export interface EvidenceGraphResponse {
  case_id?: number;
  message?: string;
  nodes: EvidenceGraphNode[];
  summary?: Record<string, unknown>;
  total_evidence?: number;
}

export interface EvidenceQueryResponse {
  query: string;
  search_type: string;
  results: EvidenceGraphNode[];
  count: number;
}

export interface EvidenceCredibilityResponse {
  evidence_id: number;
  name: string;
  credibility_score: number;
  credibility_factors: string[];
  proves_facts: string[];
  keywords: string[];
}

export async function askInsightQuestion(caseId: string | number, question: string): Promise<InsightQuestionResponse> {
  return axiosInstance.post('/api/v2/question', { case_id: Number(caseId), question }).then((res) => res.data);
}

export async function answerInsightClarification(
  caseId: string | number,
  question: string,
  answers: Record<string, string>,
): Promise<InsightQuestionResponse> {
  return axiosInstance
    .post('/api/v2/question/answer', { case_id: Number(caseId), question, answers })
    .then((res) => res.data);
}

export async function generateInsightReport(
  caseId: string | number,
  reportType = 'analysis',
  forceRegenerate = false,
): Promise<InsightReportResponse> {
  return axiosInstance
    .post('/api/v2/report/generate', {
      case_id: Number(caseId),
      report_type: reportType,
      force_regenerate: forceRegenerate,
    })
    .then((res) => res.data);
}

export async function getInsightReportStatus(
  caseId: string | number,
  reportType = 'analysis',
): Promise<InsightReportStatus> {
  return axiosInstance
    .get(`/api/v2/report/status/${caseId}`, { params: { report_type: reportType } })
    .then((res) => res.data);
}

export async function buildInsightEvidenceGraph(
  caseId: string | number,
  forceRefresh = false,
): Promise<EvidenceGraphResponse> {
  return axiosInstance
    .post('/api/v2/evidence/graph', { case_id: Number(caseId), force_refresh: forceRefresh })
    .then((res) => res.data);
}

export async function queryInsightEvidence(
  caseId: string | number,
  query: string,
  searchType = 'all',
): Promise<EvidenceQueryResponse> {
  return axiosInstance
    .get(`/api/v2/evidence/query/${caseId}`, { params: { query, search_type: searchType } })
    .then((res) => res.data);
}

export async function getInsightEvidenceCredibility(evidenceId: string | number): Promise<EvidenceCredibilityResponse> {
  return axiosInstance.get(`/api/v2/evidence/credibility/${evidenceId}`).then((res) => res.data);
}

export async function clearInsightCache(caseId: string | number): Promise<{ message: string; cleared_items: string[] }> {
  return axiosInstance.post(`/api/v2/cache/clear/${caseId}`).then((res) => res.data);
}
