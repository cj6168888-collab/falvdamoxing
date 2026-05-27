import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Deadline } from '@/types/deadline.types';

export interface TimelineMilestone {
  id: string;
  caseId: string;
  title: string;
  type: string;
  date: string;
  description?: string;
  importance?: string;
  isMilestone: boolean;
  aiSummary?: string;
}

type BackendDeadline = Partial<Deadline> & {
  id?: string | number;
  case_id?: string | number;
  deadline_type?: string;
  deadline_name?: string;
  deadline_category?: string;
  legal_basis?: string;
  start_date?: string;
  deadline_date?: string;
  status?: string;
  '期限类型'?: string;
  '期限名称'?: string;
  '分类'?: string;
  '法律依据'?: string;
  '起算日期'?: string;
  '截止日期'?: string;
  '状态'?: string;
  '关联事件'?: string;
};

type BackendTimelineMilestone = {
  id?: string | number;
  case_id?: string | number;
  event_type?: string;
  event_name?: string;
  event_date?: string;
  event_description?: string;
  importance?: string;
  is_milestone?: boolean;
  ai_summary?: string;
};

function normalizeDeadline(item: BackendDeadline, caseId: string): Deadline {
  const status = (item.status || item['状态'] || 'pending') as Deadline['status'];

  return {
    id: item.id !== undefined ? String(item.id) : '',
    caseId: String(item.caseId || item.case_id || caseId),
    title: item.title || item.deadline_name || item['期限名称'] || '未命名期限',
    type: item.type || item.deadline_type || item['期限类型'] || item.deadline_category || item['分类'] || 'deadline',
    dueDate: item.dueDate || item.deadline_date || item['截止日期'] || '',
    startDate: item.startDate || item.start_date || item['起算日期'],
    legalBasis: item.legalBasis || item.legal_basis || item['法律依据'],
    status,
    relatedTasks: item.relatedTasks || (item['关联事件'] ? [item['关联事件']] : []),
    createdAt: item.createdAt || '',
    updatedAt: item.updatedAt || '',
  };
}

function toBackendDeadline(data: Partial<Deadline>) {
  return {
    期限类型: data.type,
    期限名称: data.title,
    法律依据: data.legalBasis,
    起算日期: data.startDate,
    截止日期: data.dueDate,
  };
}

function normalizeMilestone(item: BackendTimelineMilestone, caseId: string): TimelineMilestone {
  return {
    id: item.id !== undefined ? String(item.id) : '',
    caseId: String(item.case_id || caseId),
    title: item.event_name || '未命名里程碑',
    type: item.event_type || 'milestone',
    date: item.event_date || '',
    description: item.event_description,
    importance: item.importance,
    isMilestone: item.is_milestone ?? true,
    aiSummary: item.ai_summary,
  };
}

export function useDeadlines(caseId: string) {
  return useQuery({
    queryKey: ['deadlines', caseId],
    queryFn: () =>
      axiosInstance
        .get<BackendDeadline[]>(`/api/time-control/case/${caseId}/deadlines`)
        .then((res) => res.data.map((item) => normalizeDeadline(item, caseId))),
    enabled: !!caseId,
  });
}

export async function createDeadline(caseId: string, data: Partial<Deadline>) {
  return axiosInstance
    .post(`/api/time-control/case/${caseId}/deadlines`, toBackendDeadline(data))
    .then((res) => normalizeDeadline(res.data, caseId));
}

export async function updateDeadline(deadlineId: string, data: Partial<Deadline>) {
  return axiosInstance
    .put(`/api/time-control/deadlines/${deadlineId}`, null, { params: { status: data.status } })
    .then((res) => res.data);
}

export async function generateMilestones(caseId: string) {
  return axiosInstance.post(`/api/time-control/case/${caseId}/generate-milestones`).then((res) => ({
    ...res.data,
    milestones: (res.data?.milestones || []).map(
      (item: {
        id?: string | number;
        name?: string;
        phase?: string;
        expected_date?: string;
        description?: string;
        ai_tip?: string;
      }) => ({
        id: item.id !== undefined ? String(item.id) : '',
        caseId,
        title: item.name || '未命名里程碑',
        type: item.phase || 'milestone',
        date: item.expected_date || '',
        description: item.description,
        importance: 'normal',
        isMilestone: true,
        aiSummary: item.ai_tip,
      }),
    ),
  }));
}

export async function getMilestones(caseId: string) {
  return axiosInstance
    .get<BackendTimelineMilestone[]>(`/api/time-control/case/${caseId}/milestones`)
    .then((res) => res.data.map((item) => normalizeMilestone(item, caseId)));
}

export async function getTimeline(caseId: string) {
  return axiosInstance.get(`/api/time-control/case/${caseId}/timeline`).then((res) => res.data);
}

export async function getUrgencyReport(caseId: string) {
  return axiosInstance.get(`/api/time-control/case/${caseId}/urgency-report`).then((res) => res.data);
}
