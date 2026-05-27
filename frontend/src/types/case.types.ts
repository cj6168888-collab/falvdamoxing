// 案件类型定义

export interface Case {
  id: string;
  title: string;
  type: string;
  status: 'preparing' | 'negotiating' | 'litigating' | 'appealing' | 'executing' | 'closed';
  description?: string;
  amount?: number;
  plaintiff: PartyInfo;
  defendant: PartyInfo;
  evidenceCount: number;
  documentCount: number;
  deadlineCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface PartyInfo {
  name: string;
  phone?: string;
  address?: string;
}

export interface CaseStats {
  total: number;
  inProgress: number;
  newThisMonth: number;
  inExecution: number;
}

export interface CaseFilters {
  status?: string;
  type?: string;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}
