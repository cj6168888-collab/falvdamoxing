// 对抗性分析类型

export interface Issue {
  id: string;
  caseId: string;
  title: string;
  ourPosition: string;
  opponentAttack?: string;
  keyEvidence?: string[];
  strategy?: string;
  priority: 'high' | 'medium' | 'low';
}

export interface SwotAnalysis {
  strengths: string[];
  weaknesses: string[];
  opponentWeaknesses: string[];
  opponentStrengths: string[];
}

export interface ScenarioPrediction {
  scenario: string;
  probability: number;
  description: string;
}
