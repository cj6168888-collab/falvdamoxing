import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useSeniorAnalysis(caseId: string, depth: 'quick' | 'standard' | 'deep' = 'standard') {
  return useQuery({
    queryKey: ['senior-analysis', caseId, depth],
    queryFn: () => axiosInstance.post('/api/v2/senior-analysis/analyze', {
      case_id: parseInt(caseId) || 0,
      analysis_level: depth,
    }).then(res => res.data),
    enabled: !!caseId,
  });
}
