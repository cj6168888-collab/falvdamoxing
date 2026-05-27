// 证据类型定义

export interface Evidence {
  id: string;
  caseId: string;
  name: string;
  type: string;
  source: 'own' | 'opponent' | 'third_party';
  credibilityScore?: number;
  description?: string;
  facts?: string[];
  relatedIssues?: string[];
  fileUrl?: string;
  fileSize?: number;
  fileType?: string;
  isDuplicate?: boolean;
  duplicateOf?: string;
  createdAt: string;
  updatedAt: string;
}

export interface EvidenceGap {
  type: string;
  description: string;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
}
