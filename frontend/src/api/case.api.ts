import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Case, CaseFilters } from '@/types/case.types';

interface BackendCase {
  id: number | string;
  title?: string;
  case_type?: string;
  type?: string;
  status?: string;
  description?: string;
  claim_amount?: number | string | null;
  plaintiff?: string;
  defendant?: string;
  evidence_count?: number;
  document_count?: number;
  deadline_count?: number;
  created_at?: string;
  updated_at?: string;
}

const CASE_STATUSES: Case['status'][] = [
  'preparing',
  'negotiating',
  'litigating',
  'appealing',
  'executing',
  'closed',
];

function normalizeCaseStatus(status?: string): Case['status'] {
  return CASE_STATUSES.includes(status as Case['status']) ? (status as Case['status']) : 'preparing';
}

// Transform backend response to frontend Case type
function transformCase(raw: BackendCase): Case {
  return {
    id: String(raw.id),
    title: raw.title || '',
    type: raw.case_type || raw.type || '',
    status: normalizeCaseStatus(raw.status),
    description: raw.description || '',
    amount: raw.claim_amount != null ? Number(raw.claim_amount) : 0,
    plaintiff: { name: raw.plaintiff || '' },
    defendant: { name: raw.defendant || '' },
    evidenceCount: raw.evidence_count || 0,
    documentCount: raw.document_count || 0,
    deadlineCount: raw.deadline_count || 0,
    createdAt: raw.created_at || '',
    updatedAt: raw.updated_at || '',
  };
}

export function useCases(filters?: CaseFilters) {
  return useQuery({
    queryKey: ['cases', filters],
    queryFn: () => axiosInstance.get<BackendCase[]>('/api/cases', { params: filters }).then(res => res.data.map(transformCase)),
  });
}

export function useCase(id: string) {
  return useQuery({
    queryKey: ['case', id],
    queryFn: () => axiosInstance.get<BackendCase>(`/api/cases/${id}`).then(res => transformCase(res.data)),
    enabled: !!id,
  });
}

export async function createCase(data: Partial<Case>) {
  return axiosInstance.post<Case>('/api/cases', data).then(res => res.data);
}

export async function updateCase(id: string, data: Partial<Case>) {
  return axiosInstance.put<Case>(`/api/cases/${id}`, data).then(res => res.data);
}

export async function deleteCase(id: string) {
  return axiosInstance.delete(`/api/cases/${id}`);
}

export async function closeCase(id: string) {
  return axiosInstance.post(`/api/cases/${id}/close`);
}

export async function reopenCase(id: string) {
  return axiosInstance.post(`/api/cases/${id}/reopen`);
}

export async function analyzeCase(id: string) {
  return axiosInstance.post(`/api/cases/${id}/analyze`).then(res => res.data);
}

export async function getCaseStrategy(id: string) {
  return axiosInstance.post(`/api/cases/${id}/strategy`).then(res => res.data);
}

export async function getCaseStructure(id: string) {
  return axiosInstance.get(`/api/cases/${id}/structure`).then(res => res.data);
}
