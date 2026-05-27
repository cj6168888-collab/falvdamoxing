import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ============ Appeal Hooks ============

// 获取案件的上诉列表
export function useAppeals(caseId: string, filters?: {
  status?: string;
  page?: number;
  pageSize?: number;
}) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));

  return useQuery({
    queryKey: ['appeals', caseId, filters],
    queryFn: async () => {
      const response = await fetch(`/api/case/${caseId}/appeals?${params}`);
      if (!response.ok) throw new Error('获取上诉列表失败');
      return response.json();
    },
    enabled: !!caseId,
  });
}

// 获取上诉详情
export function useAppeal(appealId: string) {
  return useQuery({
    queryKey: ['appeal', appealId],
    queryFn: async () => {
      const response = await fetch(`/api/appeal/${appealId}`);
      if (!response.ok) throw new Error('获取上诉详情失败');
      return response.json();
    },
    enabled: !!appealId,
  });
}

// 创建上诉
export function useCreateAppeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ caseId, data }: { caseId: string; data: unknown }) => {
      const response = await fetch(`/api/case/${caseId}/appeal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('创建上诉失败');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['appeals', variables.caseId] });
    },
  });
}

// 更新上诉
export function useUpdateAppeal(appealId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: unknown) => {
      const response = await fetch(`/api/appeal/${appealId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('更新上诉失败');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appeal', appealId] });
    },
  });
}

// 删除上诉
export function useDeleteAppeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ appealId }: { appealId: string; caseId: string }) => {
      const response = await fetch(`/api/appeal/${appealId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('删除上诉失败');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['appeals', variables.caseId] });
    },
  });
}

// 获取上诉期限倒计时
export function useAppealCountdown(appealId: string) {
  return useQuery({
    queryKey: ['appeal-countdown', appealId],
    queryFn: async () => {
      const response = await fetch(`/api/appeal/${appealId}/countdown`);
      if (!response.ok) throw new Error('获取倒计时失败');
      return response.json();
    },
    enabled: !!appealId,
    refetchInterval: 60000, // 每分钟刷新
  });
}

// 生成上诉状
export function useGenerateAppealDocument() {
  return useMutation({
    mutationFn: async ({ appealId, template }: { appealId: string; template?: string }) => {
      const response = await fetch(`/api/appeal/${appealId}/generate-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template }),
      });
      if (!response.ok) throw new Error('生成上诉状失败');
      return response.json();
    },
  });
}

// 更新上诉状态
export function useUpdateAppealStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      appealId,
      status,
      filedDate,
      caseNumber,
      notes,
    }: {
      appealId: string;
      status: string;
      filedDate?: string;
      caseNumber?: string;
      notes?: string;
    }) => {
      const response = await fetch(`/api/appeal/${appealId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, filed_date: filedDate, case_number: caseNumber, notes }),
      });
      if (!response.ok) throw new Error('更新状态失败');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['appeal', variables.appealId] });
      queryClient.invalidateQueries({ queryKey: ['appeals'] });
    },
  });
}

// ============ Execution Hooks ============

// 获取案件的执行记录列表
export function useExecutions(caseId: string) {
  return useQuery({
    queryKey: ['executions', caseId],
    queryFn: async () => {
      const response = await fetch(`/api/case/${caseId}/executions`);
      if (!response.ok) throw new Error('获取执行记录失败');
      return response.json();
    },
    enabled: !!caseId,
  });
}

// 获取执行记录详情
export function useExecution(executionId: string) {
  return useQuery({
    queryKey: ['execution', executionId],
    queryFn: async () => {
      const response = await fetch(`/api/execution/${executionId}`);
      if (!response.ok) throw new Error('获取执行详情失败');
      return response.json();
    },
    enabled: !!executionId,
  });
}

// 创建执行记录
export function useCreateExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ caseId, data }: { caseId: string; data: unknown }) => {
      const response = await fetch(`/api/case/${caseId}/execution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('创建执行记录失败');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['executions', variables.caseId] });
      queryClient.invalidateQueries({ queryKey: ['execution-summary', variables.caseId] });
    },
  });
}

// 更新执行记录
export function useUpdateExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ executionId, data }: { executionId: string; data: unknown }) => {
      const response = await fetch(`/api/execution/${executionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('更新执行记录失败');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['execution', variables.executionId] });
    },
  });
}

// 获取执行概况
export function useExecutionSummary(caseId: string) {
  return useQuery({
    queryKey: ['execution-summary', caseId],
    queryFn: async () => {
      const response = await fetch(`/api/case/${caseId}/execution/summary`);
      if (!response.ok) throw new Error('获取执行概况失败');
      return response.json();
    },
    enabled: !!caseId,
  });
}

// 更新执行金额
export function useUpdateExecutionAmount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      executionId,
      executedAmount,
      notes,
    }: {
      executionId: string;
      executedAmount: number;
      notes?: string;
    }) => {
      const response = await fetch(`/api/execution/${executionId}/amount`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ executed_amount: executedAmount, notes }),
      });
      if (!response.ok) throw new Error('更新金额失败');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['execution', variables.executionId] });
    },
  });
}
