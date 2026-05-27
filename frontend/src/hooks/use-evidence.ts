import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  useEvidence,
  uploadEvidence,
  updateEvidence,
  deleteEvidence,
  checkCompleteness,
  analyzeRisk,
  correctEvidence,
  getEvidenceGraph,
} from '@/api/evidence.api';

export function useEvidenceList(caseId: string) {
  return useEvidence(caseId);
}

export function useUploadEvidence(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => uploadEvidence(caseId, formData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['evidence', caseId] }),
  });
}

export function useUpdateEvidence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ evidenceId, data }: { evidenceId: string; data: Record<string, unknown> }) =>
      updateEvidence(evidenceId, data),
    onSuccess: (_, { evidenceId: _evidenceId }) => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
    },
  });
}

export function useDeleteEvidence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteEvidence,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['evidence'] }),
  });
}

export function useEvidenceCompleteness(caseId: string) {
  return useQuery({
    queryKey: ['evidence-completeness', caseId],
    queryFn: () => checkCompleteness(caseId),
    enabled: !!caseId,
  });
}

export function useEvidenceRisk(caseId: string) {
  return useQuery({
    queryKey: ['evidence-risk', caseId],
    queryFn: () => analyzeRisk(caseId),
    enabled: !!caseId,
  });
}

export function useCorrectEvidence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: correctEvidence,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['evidence'] }),
  });
}

export function useEvidenceGraph(caseId: string) {
  return useQuery({
    queryKey: ['evidence-graph', caseId],
    queryFn: () => getEvidenceGraph(caseId),
    enabled: !!caseId,
  });
}
