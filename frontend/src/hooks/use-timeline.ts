import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useTimeline(caseId: string) {
  return useQuery({
    queryKey: ['timeline', caseId],
    queryFn: () =>
      axiosInstance.get(`/api/时间把控/case/${caseId}/timeline`).then((res) => res.data),
    enabled: !!caseId,
  });
}
