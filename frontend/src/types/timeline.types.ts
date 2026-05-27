// 时间线类型

export interface Timeline {
  caseId: string;
  events: TimelineEvent[];
}

export interface TimelineEvent {
  id: string;
  date: string;
  type: string;
  title: string;
  description?: string;
  relatedEvidence?: string[];
}
