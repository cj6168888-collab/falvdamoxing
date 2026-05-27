// 执行跟踪类型 - 与后端 API 对齐

export interface ExecutionOverview {
  case_id: number;
  case_title: string;
  case_number?: string;
  execution_case_number?: string;
  execution_court?: string;
  executor_name?: string;
  executor_phone?: string;
  execution_amount?: string;
  executed_amount?: string;
  remaining_amount?: string;
  status: string;
  progress: number;
  current_stage?: string;
  total_records: number;
  total_tasks: number;
  todo_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  total_assets: number;
  controlled_assets: number;
  disposed_assets: number;
  next_follow_up?: string;
  assistance_needed?: string;
  stages: ExecutionStage[];
}

export interface ExecutionStage {
  id: number;
  case_id: number;
  stage: string;
  stage_name: string;
  start_date?: string;
  end_date?: string;
  status: string;
  description?: string;
  requirements?: Record<string, unknown>;
  completed_items?: Record<string, unknown>;
  documents?: Record<string, unknown>;
  notes?: string;
}

export interface ExecutionRecord {
  id: number;
  case_id: number;
  record_date?: string;
  record_type?: string;
  title: string;
  content?: string;
  result?: string;
  court_name?: string;
  judge_name?: string;
  document_number?: string;
  stage?: string;
  progress: number;
  attachments?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface ExecutionTask {
  id: number;
  case_id: number;
  title: string;
  description?: string;
  task_type?: string;
  stage?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'todo' | 'in_progress' | 'completed' | 'cancelled';
  due_date?: string;
  completed_date?: string;
  assignee?: string;
  related_record_id?: number;
  related_asset_id?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ExecutionAsset {
  id: number;
  case_id: number;
  asset_type?: string;
  asset_name: string;
  description?: string;
  estimated_value?: string;
  actual_value?: string;
  location?: string;
  identifier?: string;
  status: string;
  control_method?: string;
  control_date?: string;
  disposal_method?: string;
  disposal_date?: string;
  disposal_result?: string;
  source?: string;
  source_date?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export type Execution = ExecutionOverview;
