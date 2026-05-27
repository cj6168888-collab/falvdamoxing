import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useFinance(caseId: string) {
  return useQuery({
    queryKey: ['finance', caseId],
    queryFn: () => axiosInstance.get(`/api/cases/${caseId}/finance`).then((res) => res.data),
    enabled: !!caseId,
  });
}
