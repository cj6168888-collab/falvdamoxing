// 出庭抗辩类型

export interface Hearing {
  id: string;
  caseId: string;
  courtName: string;
  location?: string;
  judge?: string;
  date: string;
  type: string;
  hearingType?: string;
  status: string;
  currentPhase?: string;
  caseNumber?: string;
  participants?: unknown[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface HearingStatement {
  id: string;
  statementType: string;
  speakerRole: string;
  speakerName?: string;
  content: string;
  time?: string;
  isTrap: boolean;
  trapType?: string | null;
  suggestion?: string | null;
}

export interface TrapDetection {
  type: string;
  content: string;
  suggestion: string;
  severity: 'high' | 'medium' | 'low';
}
