import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export interface EvidenceGuideQuestion {
  id: string;
  category?: string;
  question: string;
  help_text?: string;
  options?: Array<string | { value?: string; label?: string }>;
  input_type?: string;
}

export interface EvidenceGuideGap {
  id?: string;
  missing_type?: string;
  type?: string;
  severity?: string;
  description?: string;
  suggestion?: string;
  action?: string;
  priority?: string;
}

export interface EvidenceGuideDiagnosis {
  overall_score?: number;
  readiness_level?: string;
  proof_chain_completeness?: number;
  evidence_count?: number;
  gaps_count?: number;
  critical_gaps_count?: number;
}

export interface EvidenceGuideResponse {
  case_id: number;
  diagnosis?: EvidenceGuideDiagnosis;
  evidence_analysis?: {
    submitted?: Array<{ id: string; name: string; type?: string; strength?: number; status?: string; proves?: string[] }>;
    type_distribution?: Record<string, number>;
  };
  gaps_analysis?: {
    critical?: EvidenceGuideGap[];
    important?: EvidenceGuideGap[];
    optional?: EvidenceGuideGap[];
  };
  critical_findings?: string[];
  immediate_actions?: string[];
  guidance_questions?: EvidenceGuideQuestion[];
  graph_data?: {
    nodes?: Array<Record<string, unknown>>;
    edges?: Array<Record<string, unknown>>;
    stats?: Record<string, unknown>;
  };
  diagnosed_at?: string;
}

export interface EvidenceGuideAnswerResponse {
  question_id?: string;
  answer_received?: string;
  suggestions?: Array<{
    type?: string;
    message?: string;
    action?: string;
    alternatives?: string[];
  }>;
  next_question?: EvidenceGuideQuestion | null;
  updated_diagnosis?: {
    score?: number;
    gaps_remaining?: number;
  };
}

export function useEvidenceGuide(caseId: string) {
  return useQuery({
    queryKey: ['evidence-guide', caseId],
    queryFn: () => axiosInstance.post<EvidenceGuideResponse>('/api/v2/evidence-guide/diagnose', {
      case_id: parseInt(caseId) || 0,
      force_refresh: true,
    }).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function answerGuideQuestion(
  caseId: string,
  questionId: string,
  answer: string,
): Promise<EvidenceGuideAnswerResponse> {
  return axiosInstance.post('/api/v2/evidence-guide/question/answer', {
    case_id: parseInt(caseId) || 0,
    question_id: questionId,
    answer,
  }).then(res => res.data);
}
