import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { ExecutionOverview, ExecutionRecord, ExecutionTask, ExecutionAsset } from '@/types/execution.types';

// ============ Queries ============

export function useExecutionOverview(caseId: string) {
  return useQuery({
    queryKey: ['execution-overview', caseId],
    queryFn: () => axiosInstance.get<ExecutionOverview>(`/api/execution/case/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useExecutionRecords(caseId: string) {
  return useQuery({
    queryKey: ['execution-records', caseId],
    queryFn: () => axiosInstance.get<{ records: ExecutionRecord[]; total: number }>(`/api/execution/case/${caseId}/records`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useExecutionTasks(caseId: string) {
  return useQuery({
    queryKey: ['execution-tasks', caseId],
    queryFn: () => axiosInstance.get<{ tasks: ExecutionTask[]; total: number }>(`/api/execution/case/${caseId}/tasks`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useExecutionAssets(caseId: string) {
  return useQuery({
    queryKey: ['execution-assets', caseId],
    queryFn: () => axiosInstance.get<{ assets: ExecutionAsset[]; total: number }>(`/api/execution/case/${caseId}/assets`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useExecutionStatistics(caseId: string) {
  return useQuery({
    queryKey: ['execution-statistics', caseId],
    queryFn: () => axiosInstance.get(`/api/execution/case/${caseId}/statistics`).then(res => res.data),
    enabled: !!caseId,
  });
}

// ============ Mutations ============

export function useUpdateExecutionOverview(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ExecutionOverview>) => axiosInstance.put(`/api/execution/case/${caseId}`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-overview', caseId] });
    },
  });
}

export function useCreateExecutionRecord(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ExecutionRecord>) => axiosInstance.post(`/api/execution/case/${caseId}/records`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-records', caseId] });
    },
  });
}

export function useDeleteExecutionRecord(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recordId: number) => axiosInstance.delete(`/api/execution/records/${recordId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-records', caseId] });
    },
  });
}

export function useCreateExecutionTask(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ExecutionTask>) => axiosInstance.post(`/api/execution/case/${caseId}/tasks`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-tasks', caseId] });
    },
  });
}

export function useUpdateExecutionTask(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: Partial<ExecutionTask> }) =>
      axiosInstance.put(`/api/execution/tasks/${taskId}`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-tasks', caseId] });
    },
  });
}

export function useDeleteExecutionTask(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: number) => axiosInstance.delete(`/api/execution/tasks/${taskId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-tasks', caseId] });
    },
  });
}

export function useCreateExecutionAsset(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ExecutionAsset>) => axiosInstance.post(`/api/execution/case/${caseId}/assets`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-assets', caseId] });
    },
  });
}

export function useDeleteExecutionAsset(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assetId: number) => axiosInstance.delete(`/api/execution/assets/${assetId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['execution-assets', caseId] });
    },
  });
}

export async function generateExecutionApplication(caseId: string) {
  return axiosInstance.post(`/api/execution/case/${caseId}/generate-application`).then(res => res.data);
}
