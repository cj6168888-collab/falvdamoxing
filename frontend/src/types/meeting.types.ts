// 会议类型

export interface Meeting {
  id: string;
  caseId: string;
  type: string;
  title: string;
  date: string;
  participants?: string[];
  audioUrl?: string;
  transcript?: string;
  notes?: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  createdAt: string;
  updatedAt: string;
}
