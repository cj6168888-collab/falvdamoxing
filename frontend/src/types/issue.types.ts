// 争点类型

export interface Issue {
  id: string;
  caseId: string;
  title: string;
  description?: string;
  ourPosition: string;
  opponentPosition?: string;
  keyEvidence: string[];
  strategy?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'active' | 'resolved' | 'abandoned';
  createdAt: string;
  updatedAt: string;
}
