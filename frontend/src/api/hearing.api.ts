import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Hearing, HearingStatement } from '@/types/hearing.types';

type BackendHearing = Partial<Hearing> & {
  case_id?: string | number;
  hearing_type?: string;
  hearing_date?: string;
  location?: string;
  current_phase?: string;
  case_number?: string;
  participants?: unknown[];
  庭审类型?: string;
  庭审日期?: string;
  地点?: string;
  状态?: string;
  当前阶段?: string;
};

type BackendHearingStatement = {
  id: string | number;
  发言类型?: string;
  讲话方角色?: string;
  讲话人?: string;
  内容?: string;
  时间?: string;
  是否陷阱?: boolean;
  陷阱类型?: string | null;
  建议?: string | null;
};

function normalizeHearing(raw: BackendHearing): Hearing {
  const location = raw.location || raw.地点 || raw.courtName || '';
  const hearingType = raw.hearingType || raw.hearing_type || raw.庭审类型 || raw.type || 'first_trial';

  return {
    id: String(raw.id || ''),
    caseId: String(raw.caseId || raw.case_id || ''),
    courtName: location || '未填写地点',
    location,
    judge: raw.judge,
    date: raw.date || raw.hearing_date || raw.庭审日期 || '',
    type: hearingType,
    hearingType,
    status: raw.status || raw.状态 || 'preparing',
    currentPhase: raw.currentPhase || raw.current_phase || raw.当前阶段 || '',
    caseNumber: raw.caseNumber || raw.case_number,
    participants: raw.participants,
    notes: raw.notes,
    createdAt: raw.createdAt || '',
    updatedAt: raw.updatedAt || '',
  };
}

function normalizeStatement(raw: BackendHearingStatement): HearingStatement {
  return {
    id: String(raw.id),
    statementType: raw.发言类型 || '',
    speakerRole: raw.讲话方角色 || '',
    speakerName: raw.讲话人 || '',
    content: raw.内容 || '',
    time: raw.时间 || '',
    isTrap: Boolean(raw.是否陷阱),
    trapType: raw.陷阱类型 ?? null,
    suggestion: raw.建议 ?? null,
  };
}

function toCreatePayload(data: Partial<Hearing> & Record<string, unknown>) {
  if ('庭审类型' in data || '庭审日期' in data || '地点' in data) return data;

  return {
    庭审类型: data.hearingType || data.type || 'first_trial',
    庭审日期: data.date,
    地点: data.location || data.courtName,
    案号: data.caseNumber,
    参会人员: data.participants,
  };
}

export function useHearings(caseId: string) {
  return useQuery({
    queryKey: ['hearings', caseId],
    queryFn: () => axiosInstance.get<BackendHearing[]>(`/api/hearings/case/${caseId}/hearings`).then(res => res.data.map(normalizeHearing)),
    enabled: !!caseId,
  });
}

export async function createHearing(caseId: string, data: Partial<Hearing> & Record<string, unknown>) {
  return axiosInstance.post(`/api/hearings/case/${caseId}/hearing`, toCreatePayload(data)).then(res => normalizeHearing(res.data));
}

export function useHearingStatements(hearingId: string | null) {
  return useQuery({
    queryKey: ['hearing-statements', hearingId],
    queryFn: () => axiosInstance.get<BackendHearingStatement[]>(`/api/hearings/hearing/${hearingId}/statements`).then(res => res.data.map(normalizeStatement)),
    enabled: !!hearingId,
  });
}

export async function generateOpeningStatement(caseId: string, data: unknown) {
  return axiosInstance.post(`/api/hearings/case/${caseId}/opening-statement`, data).then(res => res.data);
}

export async function detectTrap(content: string) {
  return axiosInstance.post('/api/hearings/detect-trap', { statement: content, speaker_role: 'opponent' }).then(res => res.data);
}

export async function realtimeAnalysis(content: string) {
  return axiosInstance.post('/api/hearings/realtime-analysis', { 发言内容: content, 讲话方角色: 'opponent' }).then(res => res.data);
}

export async function recordStatement(hearingId: string, data: unknown) {
  return axiosInstance.post(`/api/hearings/hearing/${hearingId}/statement`, data).then(res => res.data);
}
