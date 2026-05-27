import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createAnalysis, generateEvidenceMatrix, predictScenarios, opponentAnalysis } from '@/api/adversarial.api';

export function useCreateAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: unknown }) => createAnalysis(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['adversarial', caseId] });
    },
  });
}

export function useGenerateEvidenceMatrix() {
  return useMutation({
    mutationFn: generateEvidenceMatrix,
  });
}

export function usePredictScenarios() {
  return useMutation({
    mutationFn: predictScenarios,
  });
}

export function useOpponentAnalysis() {
  return useMutation({
    mutationFn: opponentAnalysis,
  });
}
