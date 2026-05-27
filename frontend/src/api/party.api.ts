import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Party } from '@/types/party.types';

export function useParties(caseId: string) {
  return useQuery({
    queryKey: ['parties', caseId],
    queryFn: () => axiosInstance.get<Party[]>(`/api/cases/${caseId}/parties`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function createParty(caseId: string, data: Partial<Party>) {
  return axiosInstance.post<Party>(`/api/cases/${caseId}/parties`, data).then(res => res.data);
}

export async function updateParty(caseId: string, partyId: string, data: Partial<Party>) {
  return axiosInstance.put<Party>(`/api/cases/${caseId}/parties/${partyId}`, data).then(res => res.data);
}

export async function deleteParty(caseId: string, partyId: string) {
  return axiosInstance.delete(`/api/cases/${caseId}/parties/${partyId}`);
}
