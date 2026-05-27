// 质证意见类型

export interface CrossExamination {
  id: string;
  hearingId: string;
  evidenceId: string;
  evidenceName: string;
  authenticity: 'accept' | 'object';
  legality: 'accept' | 'object';
  relevance: 'accept' | 'object';
  opinion?: string;
  createdAt: string;
}
