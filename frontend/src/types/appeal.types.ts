// 上诉追踪类型 - 与后端 API 对齐

export interface Appeal {
  id: number;
  case_id: number;
  appeal_type: 'first_to_second' | 'second_to_retrial' | 'retrial';
  appeal_reason: 'factual_error' | 'legal_error' | 'procedural' | 'new_evidence' | 'insufficient' | 'other';
  original_case_number?: string;
  original_court?: string;
  original_judge?: string;
  original_judgment_date?: string;
  original_judgment_content?: string;
  appellant_type?: string;
  appellant_name?: string;
  judgment_received_date?: string;
  appeal_deadline?: string;
  appeal_submitted_date?: string;
  appeal_accepted_date?: string;
  hearing_date?: string;
  appeal_decision_date?: string;
  status: 'preparing' | 'submitted' | 'accepted' | 'hearing' | 'decided' | 'rejected' | 'withdrawn';
  days_remaining?: number;
  is_overdue: boolean;
  appeal_petition?: string;
  appeal_facts?: string;
  new_evidence_list?: string;
  original_evidence_used?: string;
  appeal_requests?: string;
  original_requests?: string;
  modified_requests?: string;
  grounds_of_appeal?: Record<string, unknown>;
  opposing_arguments?: string;
  key_disputes?: Record<string, unknown>;
  strategy?: string;
  key_arguments?: Record<string, unknown>;
  evidence_plan?: Record<string, unknown>;
  milestones?: Record<string, unknown>;
  decision?: string;
  decision_type?: string;
  favorable_outcome?: boolean;
  argument_count?: number;
  document_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AppealArgument {
  id: number;
  appeal_record_id: number;
  argument_type: string;
  title: string;
  description?: string;
  original_finding?: string;
  appeal_finding?: string;
  discrepancy?: string;
  supporting_evidence?: Record<string, unknown>;
  counter_evidence?: Record<string, unknown>;
  legal_basis?: Record<string, unknown>;
  reasoning?: string;
  expected_opposition?: string;
  counter_response?: string;
  importance: 'high' | 'medium' | 'low';
  success_probability?: number;
  is_key_argument: boolean;
  status: 'draft' | 'submitted' | 'accepted' | 'rejected';
  ai_suggestions?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AppealDeadline {
  id: number;
  appeal_record_id: number;
  deadline_type: string;
  deadline_name: string;
  deadline_date?: string;
  description?: string;
  legal_basis?: string;
  status: 'pending' | 'active' | 'expired' | 'completed';
  days_remaining?: number;
  is_mandatory: boolean;
  reminder_days?: number[];
}

export interface AppealDocument {
  id: number;
  appeal_record_id: number;
  document_type: string;
  document_name: string;
  description?: string;
  source?: string;
  status: 'pending' | 'prepared' | 'submitted' | 'accepted' | 'rejected';
  is_required: boolean;
  related_document_id?: number;
  purpose?: string;
  content_summary?: string;
  key_points?: Record<string, unknown>;
  ai_summary?: string;
  ai_suggestions?: string;
}

export interface SecondTrialStrategy {
  id: number;
  appeal_record_id: number;
  title: string;
  target_arguments?: unknown[];
  defense_points?: unknown[];
  defense_reasoning?: string;
  supporting_evidence?: Record<string, unknown>;
  counter_evidence?: Record<string, unknown>;
  legal_basis?: Record<string, unknown>;
  expected_outcome?: string;
  favorable_arguments?: Record<string, unknown>;
  is_approved: boolean;
}

export interface AppealCountdown {
  appeal_id: number;
  status: string;
  judgment_received_date?: string;
  appeal_deadline?: {
    deadline_date: string;
    days_remaining: number;
    hours_remaining: number;
    is_overdue: boolean;
  };
  appeal_submitted_date?: string;
  hearing_date?: string;
  deadlines: AppealDeadline[];
}

export interface AppealStatistics {
  total_appeals: number;
  appeals_by_status: Record<string, number>;
  total_arguments: number;
  key_arguments: number;
  total_documents: number;
  prepared_documents: number;
}
