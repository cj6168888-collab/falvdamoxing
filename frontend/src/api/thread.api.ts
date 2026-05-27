import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { CaseThread, CounterClaim } from '@/types/thread.types';

export function useThreads(caseId: string) {
  return useQuery({
    queryKey: ['threads', caseId],
    queryFn: () => axiosInstance.get<CaseThread[]>(`/api/cases/${caseId}/threads`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useCounterClaims(caseId: string) {
  return useQuery({
    queryKey: ['counter-claims', caseId],
    queryFn: () => axiosInstance.get<CounterClaim[]>(`/api/cases/${caseId}/counter-claims`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function createThread(caseId: string, data: Partial<CaseThread>) {
  return axiosInstance.post(`/api/cases/${caseId}/threads`, data).then(res => res.data);
}

export async function updateThread(caseId: string, threadId: string, data: Partial<CaseThread>) {
  return axiosInstance.put(`/api/cases/${caseId}/threads/${threadId}`, data).then(res => res.data);
}

export async function createCounterClaim(caseId: string, data: Partial<CounterClaim>) {
  return axiosInstance.post(`/api/cases/${caseId}/counter-claims`, data).then(res => res.data);
}

export async function updateCounterClaim(caseId: string, claimId: string, data: Partial<CounterClaim>) {
  return axiosInstance.put(`/api/cases/${caseId}/counter-claims/${claimId}`, data).then(res => res.data);
}
