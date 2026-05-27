import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateCase, deleteCase } from '@/api/case.api';

export function useCaseActions() {
  const queryClient = useQueryClient();

  const deleteCaseMutation = useMutation({
    mutationFn: deleteCase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });

  const updateCaseMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      updateCase(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });

  return {
    deleteCase: deleteCaseMutation,
    updateCase: updateCaseMutation,
  };
}
