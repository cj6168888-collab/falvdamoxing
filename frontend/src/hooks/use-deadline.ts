import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createDeadline, updateDeadline, generateMilestones } from '@/api/timeline.api';
import { useDeadlines } from '@/api/timeline.api';

export function useDeadlineList(caseId: string) {
  return useDeadlines(caseId);
}

export function useCreateDeadline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) => createDeadline(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['deadlines', caseId] });
    },
  });
}

export function useUpdateDeadline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ deadlineId, data }: { deadlineId: string; data: Record<string, unknown> }) => updateDeadline(deadlineId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deadlines'] });
    },
  });
}

export function useGenerateMilestones() {
  return useMutation({
    mutationFn: generateMilestones,
  });
}
