import { useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { useAppeals, useAppealArguments } from '@/api/appeal.api';

export function useAppealList(caseId: string) {
  return useAppeals(caseId);
}

export function useAppealArgumentsList(caseId: string) {
  return useAppealArguments(caseId);
}

export function useCreateAppeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) =>
      axiosInstance.post(`/api/appeal/case/${caseId}/appeals`, data).then(res => res.data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['appeals', caseId] });
    },
  });
}

export function useCreateAppealArgument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> }) =>
      axiosInstance.post(`/api/appeal/case/${caseId}/arguments`, data).then(res => res.data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['appeal-arguments', caseId] });
    },
  });
}

export function useUpdateAppealArgument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ argumentId, data }: { argumentId: string; data: Record<string, unknown> }) =>
      axiosInstance.put(`/api/appeal/argument/${argumentId}`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal-arguments'] });
    },
  });
}
