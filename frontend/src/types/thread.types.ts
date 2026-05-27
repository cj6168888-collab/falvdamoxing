// 线索与反诉类型定义

export interface CaseThread {
  id: string;
  caseId: string;
  title: string;
  description?: string;
  status: 'active' | 'completed' | 'abandoned';
  priority: 'high' | 'medium' | 'low';
  createdAt: string;
  updatedAt: string;
}

export interface CounterClaim {
  id: string;
  caseId: string;
  title: string;
  description?: string;
  amount?: number;
  status: 'pending' | 'filed' | 'accepted' | 'rejected';
  createdAt: string;
  updatedAt: string;
}
