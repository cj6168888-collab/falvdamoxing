import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCaseStore } from '@/stores/case.store';
import { useCases, useCase, createCase, updateCase, deleteCase } from '@/api/case.api';
import type { Case, CaseFilters } from '@/types/case.types';

export function useCaseList(filters?: CaseFilters) {
  return useCases(filters);
}

export function useCaseDetail(id: string) {
  return useCase(id);
}

export function useCreateCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cases'] }),
  });
}

export const useCaseCreate = useCreateCase;

export function useUpdateCase(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Case>) => updateCase(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case', id] });
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });
}

export function useDeleteCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cases'] }),
  });
}

export function useCurrentCase() {
  return useCaseStore((state) => state.currentCase);
}
