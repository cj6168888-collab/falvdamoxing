import { useSeniorAnalysis } from '@/api/senior-analysis.api';

export function useSeniorAnalysisHook(caseId: string, depth: 'quick' | 'standard' | 'deep' = 'standard') {
  return useSeniorAnalysis(caseId, depth);
}
