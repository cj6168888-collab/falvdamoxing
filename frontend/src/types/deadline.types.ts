// 时间把控类型

export interface Deadline {
  id: string;
  caseId: string;
  title: string;
  type: string;
  dueDate: string;
  startDate?: string;
  legalBasis?: string;
  status: 'pending' | 'active' | 'completed' | 'overdue' | 'expired' | 'extended' | 'suspended';
  relatedTasks?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface InterruptEvent {
  id: string;
  deadlineId: string;
  type: string;
  date: string;
  description: string;
  newDueDate?: string;
}
