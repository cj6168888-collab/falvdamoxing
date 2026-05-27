// 资深分析类型

export interface SeniorAnalysis {
  caseId: string;
  depth: 'quick' | 'standard' | 'deep';
  caseUnderstanding: string;
  coreDispute: string;
  keyEvidence: string[];
  legalRequirements: LegalRequirement[];
  strategySuggestions: string[];
  riskWarnings: string[];
  generatedAt: string;
}

export interface LegalRequirement {
  name: string;
  status: 'met' | 'partial' | 'unmet';
  risk: 'low' | 'medium' | 'high';
  description?: string;
}
