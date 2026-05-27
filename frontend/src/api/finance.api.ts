import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { FinanceOverview, ExpenseRecord, CostBenefitAnalysis, WinRateAssessment } from '@/types/finance.types';

// ============ Queries ============

export function useFinanceOverview(caseId: string) {
  return useQuery({
    queryKey: ['finance-overview', caseId],
    queryFn: () => axiosInstance.get<FinanceOverview>(`/api/finance/case/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useExpenses(caseId: string) {
  return useQuery({
    queryKey: ['expenses', caseId],
    queryFn: () => axiosInstance.get<{ expenses: ExpenseRecord[]; total: number }>(`/api/finance/case/${caseId}/expenses`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useCostAnalysis(caseId: string) {
  return useQuery({
    queryKey: ['cost-analysis', caseId],
    queryFn: () => axiosInstance.get<CostBenefitAnalysis>(`/api/finance/case/${caseId}/cost-analysis`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useWinRate(caseId: string) {
  return useQuery({
    queryKey: ['win-rate', caseId],
    queryFn: () => axiosInstance.get<{ win_rate?: number; win_rate_confidence?: number; win_rate_assessed_at?: string; latest_assessment?: WinRateAssessment }>(`/api/finance/case/${caseId}/win-rate`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useFinanceStatistics(caseId: string) {
  return useQuery({
    queryKey: ['finance-statistics', caseId],
    queryFn: () => axiosInstance.get(`/api/finance/case/${caseId}/statistics`).then(res => res.data),
    enabled: !!caseId,
  });
}

// ============ Mutations ============

export function useUpdateFinanceOverview(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { expected_recovery?: number; actual_recovery?: number; notes?: string }) =>
      axiosInstance.put(`/api/finance/case/${caseId}`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance-overview', caseId] });
    },
  });
}

export function useCreateExpense(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ExpenseRecord>) => axiosInstance.post(`/api/finance/case/${caseId}/expenses`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses', caseId] });
      queryClient.invalidateQueries({ queryKey: ['finance-overview', caseId] });
    },
  });
}

export function useUpdateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ expenseId, data }: { expenseId: number; data: Partial<ExpenseRecord> }) =>
      axiosInstance.put(`/api/finance/expenses/${expenseId}`, data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      queryClient.invalidateQueries({ queryKey: ['finance-overview'] });
    },
  });
}

export function useDeleteExpense(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (expenseId: number) => axiosInstance.delete(`/api/finance/expenses/${expenseId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses', caseId] });
      queryClient.invalidateQueries({ queryKey: ['finance-overview', caseId] });
    },
  });
}

export function useAssessWinRate(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (force: boolean = false) => axiosInstance.post(`/api/finance/case/${caseId}/win-rate`, null, { params: { force } }).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['win-rate', caseId] });
      queryClient.invalidateQueries({ queryKey: ['finance-overview', caseId] });
    },
  });
}
