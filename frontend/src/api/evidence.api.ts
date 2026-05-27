import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Evidence } from '@/types/evidence.types';

export interface EvidenceGraphNode {
  id: string;
  label?: string;
  name?: string;
  title?: string;
  type?: string;
  category?: string;
  credibility?: number;
  credibility_score?: number;
  strength?: number;
  status?: string;
  color?: string;
}

export interface EvidenceGraphEdge {
  id?: string;
  source: string;
  target: string;
  type?: string;
  label?: string;
}

export interface EvidenceGraphResponse {
  nodes?: EvidenceGraphNode[];
  edges?: EvidenceGraphEdge[];
  legend?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  stats?: Record<string, unknown>;
}

export interface EvidenceQuestionResponse {
  answer?: string;
  message?: string;
  status?: string;
  type?: string;
  conversation_id?: string;
  needs_redirect?: boolean;
  redirect_suggestion?: string;
  topic_analysis?: {
    scope?: string;
    relevance_score?: number;
    reason?: string;
  };
  suggested_questions?: string[];
}

type EvidenceListResponse = Evidence[] | {
  evidence_list?: Evidence[];
  items?: Evidence[];
};

function normalizeEvidenceList(data: EvidenceListResponse): Evidence[] {
  if (Array.isArray(data)) return data;
  const list = data.evidence_list || data.items || [];
  return Array.isArray(list) ? list : [];
}

export function useEvidence(caseId: string) {
  return useQuery({
    queryKey: ['evidence', caseId],
    queryFn: () => axiosInstance.get<EvidenceListResponse>(`/api/v2/evidence-graph/evidence/list`, { params: { case_id: parseInt(caseId) || 0 } }).then(res => normalizeEvidenceList(res.data)),
    enabled: !!caseId,
  });
}

export function useEvidenceCount(caseId: string) {
  return useQuery({
    queryKey: ['evidence-count', caseId],
    queryFn: () => axiosInstance.get<EvidenceListResponse>(`/api/v2/evidence-graph/evidence/list`, { params: { case_id: parseInt(caseId) || 0 } }).then(res => normalizeEvidenceList(res.data).length),
    enabled: !!caseId,
  });
}

export async function uploadEvidence(caseId: string, formData: FormData) {
  return axiosInstance.post(`/api/documents/upload-batch/${caseId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data);
}

export async function updateEvidence(evidenceId: string, data: Partial<Evidence>) {
  return axiosInstance.put(`/api/v2/evidence-graph/evidence/update`, { id: evidenceId, ...data }).then(res => res.data);
}

export async function deleteEvidence(evidenceId: string) {
  return axiosInstance.delete(`/api/evidence/${evidenceId}`);
}

export async function checkCompleteness(caseId: string) {
  return axiosInstance.post('/api/evidence/check-completeness', { caseId }).then(res => res.data);
}

export async function analyzeRisk(caseId: string) {
  return axiosInstance.post(`/api/evidence/risk-analyze/${caseId}`).then(res => res.data);
}

export async function correctEvidence(data: { evidenceId: string; corrections: Record<string, unknown> }) {
  return axiosInstance.post('/api/v2/evidence-graph/evidence/correct', data).then(res => res.data);
}

export async function getEvidenceGraph(caseId: string, viewType = 'default'): Promise<EvidenceGraphResponse> {
  return axiosInstance.get('/api/v2/evidence-graph/graph/data', {
    params: { case_id: parseInt(caseId) || 0, view_type: viewType },
  }).then(res => res.data);
}

export async function analyzeEvidenceRelationships(caseId: string) {
  return axiosInstance.post('/api/v2/evidence-graph/relationships/analyze', {
    case_id: parseInt(caseId) || 0,
    force_refresh: true,
  }).then(res => res.data);
}

export async function askEvidenceQuestion(
  caseId: string,
  question: string,
  conversationId?: string,
): Promise<EvidenceQuestionResponse> {
  return axiosInstance.post('/api/evidence/qa', {
    case_id: parseInt(caseId) || 0,
    question,
    conversation_id: conversationId,
  }).then(res => res.data);
}
