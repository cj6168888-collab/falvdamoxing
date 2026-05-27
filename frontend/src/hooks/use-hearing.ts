import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createHearing, detectTrap, realtimeAnalysis, recordStatement } from '@/api/hearing.api';
import { useHearings, useHearingStatements } from '@/api/hearing.api';

export function useHearingList(caseId: string) {
  return useHearings(caseId);
}

export function useHearingStatementList(hearingId: string | null) {
  return useHearingStatements(hearingId);
}

export function useCreateHearing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createHearing(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['hearings', caseId] });
    },
  });
}

export function useDetectTrap() {
  return useMutation({
    mutationFn: detectTrap,
  });
}

export function useRealtimeAnalysis() {
  return useMutation({
    mutationFn: realtimeAnalysis,
  });
}

export function useRecordStatement() {
  return useMutation({
    mutationFn: ({ hearingId, data }: { hearingId: string; data: unknown }) => recordStatement(hearingId, data),
  });
}
