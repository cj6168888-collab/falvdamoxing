import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createCounterClaim, updateCounterClaim } from '@/api/thread.api';
export function useCreateCounterClaim() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createCounterClaim(caseId, data), onSuccess: (_, { caseId }) => { qc.invalidateQueries({ queryKey: ['counter-claims', caseId] }); } }); }
export function useUpdateCounterClaim() { const qc = useQueryClient(); return useMutation({ mutationFn: ({ caseId, claimId, data }: { caseId: string; claimId: string; data: Record<string, unknown> }) => updateCounterClaim(caseId, claimId, data), onSuccess: () => { qc.invalidateQueries({ queryKey: ['counter-claims'] }); } }); }
