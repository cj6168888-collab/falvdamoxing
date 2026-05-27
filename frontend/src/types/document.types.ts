// 文书类型定义

export interface Document {
  id: string;
  caseId: string;
  title: string;
  type: string;
  content: string;
  version: number;
  status: 'draft' | 'review' | 'final';
  relatedEvidence?: string[];
  relatedIssues?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface DocumentTemplate {
  id: string;
  name: string;
  type: string;
  description: string;
  category: string;
}
