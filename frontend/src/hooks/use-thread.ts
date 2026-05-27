import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createThread, updateThread, createCounterClaim, updateCounterClaim } from '@/api/thread.api';
import { useThreads, useCounterClaims } from '@/api/thread.api';

export function useThreadList(caseId: string) {
  return useThreads(caseId);
}

export function useCounterClaimList(caseId: string) {
  return useCounterClaims(caseId);
}

export function useCreateThread() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createThread(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['threads', caseId] });
    },
  });
}

export function useUpdateThread() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, threadId, data }: { caseId: string; threadId: string; data: Record<string, unknown> }) =>
      updateThread(caseId, threadId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threads'] });
    },
  });
}

export function useCreateCounterClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createCounterClaim(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['counter-claims', caseId] });
    },
  });
}

export function useUpdateCounterClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, claimId, data }: { caseId: string; claimId: string; data: Record<string, unknown> }) =>
      updateCounterClaim(caseId, claimId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['counter-claims'] });
    },
  });
}
