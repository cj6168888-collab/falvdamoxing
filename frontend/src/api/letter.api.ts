import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Letter } from '@/types/letter.types';

function toCreateLetterPayload(data: Partial<Letter>) {
  return {
    标题: data.title || '',
    方向: data.direction || 'outgoing',
    类型: data.letter_type || 'other',
    文号: data.reference_number || undefined,
    发送方: data.sender || undefined,
    接收方: data.recipient || undefined,
    函件日期: data.letter_date || undefined,
    收到日期: data.received_date || undefined,
    截止日期: data.deadline || undefined,
    内容摘要: data.content_summary || undefined,
    核心诉求: data.key_demands || undefined,
  };
}

export function useLetters(caseId: string) {
  return useQuery({
    queryKey: ['letters', caseId],
    queryFn: () => axiosInstance.get<Letter[]>(`/api/time-control/case/${caseId}/letters`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function createLetter(caseId: string, data: Partial<Letter>) {
  return axiosInstance.post(`/api/time-control/case/${caseId}/letters`, toCreateLetterPayload(data)).then(res => res.data);
}

export async function updateLetter(_caseId: string, letterId: string, data: Partial<Letter>) {
  return axiosInstance.put(`/api/time-control/letters/${letterId}`, data).then(res => res.data);
}

export async function deleteLetter(_caseId: string, letterId: string) {
  return axiosInstance.delete(`/api/time-control/letters/${letterId}`).then(res => res.data);
}

export async function updateMailing(letterId: string, data: unknown) {
  return axiosInstance.post(`/api/time-control/letters/${letterId}/mailing`, data);
}

export async function confirmDelivered(letterId: string) {
  return axiosInstance.post(`/api/time-control/letters/${letterId}/delivered`);
}

export async function generateReply(letterId: string) {
  return axiosInstance.post(`/api/time-control/letters/${letterId}/generate-reply`).then(res => res.data);
}

export async function updateReply(letterId: string, data: unknown) {
  return axiosInstance.post(`/api/time-control/letters/${letterId}/reply`, data);
}

export async function analyzeReply(letterId: string) {
  return axiosInstance.post(`/api/time-control/letters/${letterId}/ai-analyze-reply`).then(res => res.data);
}

export async function getMailTracking(caseId: string) {
  return axiosInstance.get(`/api/time-control/case/${caseId}/mail-tracking`).then(res => res.data);
}

export async function getUrgencyReport(caseId: string) {
  return axiosInstance.get(`/api/time-control/case/${caseId}/urgency-report`).then(res => res.data);
}

export async function discoverLetters(caseId: string) {
  return axiosInstance.post(`/api/time-control/case/${caseId}/letters/discover`).then(res => res.data);
}

export async function getDiscoveryStatus(caseId: string) {
  return axiosInstance.get(`/api/time-control/case/${caseId}/letters/discovery-status`).then(res => res.data);
}
