import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Appeal, AppealArgument, AppealDeadline, AppealDocument, SecondTrialStrategy, AppealCountdown, AppealStatistics } from '@/types/appeal.types';

// ============ Queries ============

export function useAppeals(caseId: string) {
  return useQuery({
    queryKey: ['appeals', caseId],
    queryFn: () => axiosInstance.get<{ appeals: Appeal[]; total: number }>(`/api/appeal/case/${caseId}/appeals`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useAppeal(appealId: string) {
  return useQuery({
    queryKey: ['appeal', appealId],
    queryFn: () => axiosInstance.get<{ appeal: Appeal }>(`/api/appeal/appeals/${appealId}`).then(res => res.data.appeal),
    enabled: !!appealId,
  });
}

export function useAppealArguments(caseId: string) {
  return useQuery({
    queryKey: ['appeal-arguments', caseId],
    queryFn: () => axiosInstance.get<{ arguments: AppealArgument[]; total: number }>(`/api/appeal/case/${caseId}/arguments`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useAppealDeadlines(appealId: string) {
  return useQuery({
    queryKey: ['appeal-deadlines', appealId],
    queryFn: () => axiosInstance.get<{ deadlines: AppealDeadline[]; total: number }>(`/api/appeal/appeal/${appealId}/deadlines`).then(res => res.data),
    enabled: !!appealId,
  });
}

export function useAppealDocuments(appealId: string) {
  return useQuery({
    queryKey: ['appeal-documents', appealId],
    queryFn: () => axiosInstance.get<{ documents: AppealDocument[]; total: number }>(`/api/appeal/appeal/${appealId}/documents`).then(res => res.data),
    enabled: !!appealId,
  });
}

export function useAppealStrategy(appealId: string) {
  return useQuery({
    queryKey: ['appeal-strategy', appealId],
    queryFn: () => axiosInstance.get<{ strategy: SecondTrialStrategy | null }>(`/api/appeal/appeal/${appealId}/strategy`).then(res => res.data.strategy),
    enabled: !!appealId,
  });
}

export function useAppealCountdown(appealId: string) {
  return useQuery({
    queryKey: ['appeal-countdown', appealId],
    queryFn: () => axiosInstance.get<AppealCountdown>(`/api/appeal/appeal/${appealId}/countdown`).then(res => res.data),
    enabled: !!appealId,
    refetchInterval: 60000,
  });
}

export function useAppealStatistics(caseId: string) {
  return useQuery({
    queryKey: ['appeal-statistics', caseId],
    queryFn: () => axiosInstance.get<AppealStatistics>(`/api/appeal/case/${caseId}/statistics`).then(res => res.data),
    enabled: !!caseId,
  });
}

// ============ Mutations ============

export function useCreateAppeal(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Appeal>) => axiosInstance.post(`/api/appeal/case/${caseId}/appeals`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeals', caseId] });
    },
  });
}

export function useUpdateAppeal(appealId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Appeal>) => axiosInstance.put(`/api/appeal/appeals/${appealId}`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal', String(appealId)] });
    },
  });
}

export function useDeleteAppeal(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (appealId: number) => axiosInstance.delete(`/api/appeal/appeals/${appealId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeals', caseId] });
    },
  });
}

export function useCreateAppealArgument(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<AppealArgument>) => axiosInstance.post(`/api/appeal/case/${caseId}/arguments`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal-arguments', caseId] });
    },
  });
}

export function useUpdateAppealArgument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ argumentId, data }: { argumentId: number; data: Partial<AppealArgument> }) =>
      axiosInstance.put(`/api/appeal/argument/${argumentId}`, data).then(res => res.data),
    onSuccess: (_, { argumentId }) => {
      queryClient.invalidateQueries({ queryKey: ['appeal-argument', String(argumentId)] });
    },
  });
}

export function useDeleteAppealArgument(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (argumentId: number) => axiosInstance.delete(`/api/appeal/argument/${argumentId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal-arguments', caseId] });
    },
  });
}

export function useCreateAppealDeadline(appealId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<AppealDeadline>) => axiosInstance.post(`/api/appeal/appeal/${appealId}/deadlines`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal-deadlines', appealId] });
    },
  });
}

export function useCreateAppealDocument(appealId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<AppealDocument>) => axiosInstance.post(`/api/appeal/appeal/${appealId}/documents`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal-documents', appealId] });
    },
  });
}

export function useCreateAppealStrategy(appealId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<SecondTrialStrategy>) => axiosInstance.post(`/api/appeal/appeal/${appealId}/strategy`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal-strategy', appealId] });
    },
  });
}

// ============ Direct API calls (non-hook) ============

export async function generateAppealPetition(appealId: string) {
  return axiosInstance.post(`/api/appeal/appeal/${appealId}/generate-petition`).then(res => res.data);
}
