import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createLetter, updateLetter, deleteLetter, generateReply } from '@/api/letter.api';
import { useLetters } from '@/api/letter.api';

export function useLetterList(caseId: string) {
  return useLetters(caseId);
}

export function useCreateLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createLetter(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['letters', caseId] });
    },
  });
}

export function useUpdateLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, letterId, data }: { caseId: string; letterId: string; data: Record<string, unknown> }) => updateLetter(caseId, letterId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['letters', caseId] });
    },
  });
}

export function useDeleteLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, letterId }: { caseId: string; letterId: string }) => deleteLetter(caseId, letterId),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['letters', caseId] });
    },
  });
}

export function useGenerateReply() {
  return useMutation({
    mutationFn: generateReply,
  });
}
