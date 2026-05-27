// 案件财务类型 - 与后端 API 对齐

export interface FinanceOverview {
  case_id: number;
  case_title: string;
  claim_amount?: string;
  finance: {
    id: number;
    total_expenses: number;
    total_paid: number;
    total_pending: number;
    total_reimbursed: number;
    expected_recovery?: number;
    actual_recovery?: number;
    cost_benefit_ratio?: number;
    net_benefit?: number;
    win_rate?: number;
    win_rate_confidence?: number;
    win_rate_assessed_at?: string;
    notes?: string;
    updated_at?: string;
  };
  expenses_by_category: Record<string, { count: number; total: number }>;
  expenses_by_status: Record<string, number>;
  latest_win_rate?: {
    win_rate: number;
    confidence: number;
    assessed_at: string;
  };
}

export interface ExpenseRecord {
  id: number;
  case_id: number;
  category?: string;
  title: string;
  description?: string;
  amount: number;
  currency: string;
  status: 'pending' | 'paid' | 'reimbursed' | 'refunded';
  expense_date?: string;
  payment_date?: string;
  due_date?: string;
  payee?: string;
  invoice_number?: string;
  related_document_id?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface WinRateAssessment {
  id: number;
  case_id: number;
  win_rate: number;
  confidence: number;
  factors?: Array<{ factor: string; score: number; weight: number; analysis: string }>;
  overall_analysis?: string;
  evidence_strength?: number;
  legal_basis_strength?: number;
  procedural_compliance?: number;
  opponent_weakness?: number;
  precedent_support?: number;
  key_risks?: string[];
  risk_mitigation?: string;
  assessment_method: string;
  assessor?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CostBenefitAnalysis {
  case_id: number;
  case_title: string;
  claim_amount?: string;
  total_expenses: number;
  expected_recovery?: number;
  actual_recovery?: number;
  cost_benefit_ratio?: number;
  net_benefit?: number;
  roi?: number;
  expense_breakdown: Record<string, { amount: number; count: number; percentage: number }>;
  monthly_trend: Record<string, number>;
  expense_count: number;
}

export interface FinanceStatistics {
  case_id: number;
  total_expenses: number;
  average_expense: number;
  expense_count: number;
  max_expense: number;
  min_expense: number;
  expenses_by_category: Record<string, { count: number; total: number }>;
  expenses_by_status: Record<string, number>;
}
