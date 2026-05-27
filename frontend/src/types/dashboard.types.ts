export interface UrgentItem {
  id: string;
  type: string;
  title: string;
  description?: string;
  case_id?: number;
  case_title?: string;
  priority?: string;
  trigger_date?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface UpcomingTask {
  id: string;
  type: string;
  title: string;
  description?: string;
  case_id?: number;
  case_title?: string;
  due_date?: string;
  days_until?: number;
  priority?: string;
  caseId?: string;
  caseTitle?: string;
  dueDate?: string;
  daysRemaining?: number;
  redirectPath?: string;
}

export interface RecentCase {
  id: number;
  case_number?: string;
  title: string;
  case_type: string;
  status: string;
  cause?: string;
  plaintiff?: string;
  defendant?: string;
  claim_amount?: string;
  document_count: number;
  evidence_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface ActivityLog {
  type: string;
  title: string;
  description: string;
  case_id?: number;
  timestamp?: string;
}

export interface DashboardStats {
  total_cases: number;
  active_cases: number;
  closed_cases: number;
  execution_cases: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  total_documents: number;
  total_evidence: number;
  total_reminders: number;
  unread_reminders: number;
  uncompleted_reminders: number;
  high_priority_reminders: number;
}

export interface DashboardData {
  stats: DashboardStats;
  urgent_items: UrgentItem[];
  upcoming_tasks: UpcomingTask[];
  recent_cases: RecentCase[];
  activity_log: ActivityLog[];
  generated_at: string;
}

export interface TodaySuggestion {
  id: string;
  title: string;
  description: string;
  suggestion?: string;
  type: string;
  priority: 'high' | 'medium' | 'low';
  actionUrl?: string;
  caseId?: string;
  caseTitle?: string;
}

export interface UrgentTask {
  id: string;
  type: 'appeal' | 'evidence' | 'hearing' | 'filing' | 'response' | 'other';
  title: string;
  description?: string;
  priority?: string;
  caseId?: string;
  caseTitle?: string;
  dueDate?: string;
  daysRemaining: number;
  redirectPath: string;
}
