// 提醒类型 - 与后端 API 对齐

export interface Reminder {
  id: number;
  case_id?: number;
  case_title?: string;
  reminder_type: 'deadline' | 'material_missing' | 'hearing' | 'evidence' | 'risk' | 'opportunity' | 'strategy';
  priority: 'high' | 'medium' | 'low';
  title: string;
  content: string;
  suggestion?: string;
  trigger_date?: string;
  is_triggered: boolean;
  is_read: boolean;
  is_completed: boolean;
  is_overdue?: boolean;
  days_until_trigger?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ReminderStats {
  total: number;
  unread: number;
  uncompleted: number;
  completed: number;
  high_priority: number;
  overdue: number;
  upcoming_7d: number;
  by_type: Record<string, number>;
}

export interface ReminderCreate {
  case_id?: number;
  reminder_type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  content: string;
  trigger_date?: string;
}

export interface ReminderUpdate {
  id: number;
  title?: string;
  content?: string;
  priority?: 'high' | 'medium' | 'low';
  is_completed?: boolean;
  is_read?: boolean;
}

export interface ReminderBatchAction {
  ids: number[];
  action: 'complete' | 'delete' | 'mark_read';
}
