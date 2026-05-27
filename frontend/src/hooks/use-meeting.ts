import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useMeeting(caseId: string) {
  return useQuery({
    queryKey: ['meeting', caseId],
    queryFn: () => axiosInstance.get(`/api/meetings/case/${caseId}`).then((res) => res.data),
    enabled: !!caseId,
  });
}
