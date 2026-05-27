import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createParty, updateParty, deleteParty } from '@/api/party.api';
import { useParties } from '@/api/party.api';

export function usePartyList(caseId: string) {
  return useParties(caseId);
}

export function useCreateParty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createParty(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['parties', caseId] });
    },
  });
}

export function useUpdateParty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, partyId, data }: { caseId: string; partyId: string; data: Record<string, unknown> }) => updateParty(caseId, partyId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['parties', caseId] });
    },
  });
}

export function useDeleteParty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, partyId }: { caseId: string; partyId: string }) => deleteParty(caseId, partyId),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['parties', caseId] });
    },
  });
}
