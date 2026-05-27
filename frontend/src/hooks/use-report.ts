import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  useReports,
  useReportDetail as useReportDetailQuery,
  generateReport,
  cancelReport,
  deleteReport,
  regenerateReport,
  getReportStatus,
} from '@/api/report.api';

/**
 * 获取报告列表 Hook
 */
export function useReportList(caseId: string) {
  return useReports(caseId);
}

/**
 * 获取报告详情 Hook
 */
export function useReportDetail(reportId: string) {
  return useReportDetailQuery(reportId);
}

/**
 * 获取报告生成状态 Hook
 */
export function useReportStatus(caseId: string, reportType: string = 'analysis') {
  return useQuery({
    queryKey: ['report-status', caseId, reportType],
    queryFn: () => getReportStatus(caseId, reportType),
    enabled: !!caseId,
    // 轮询直到报告生成完成
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'GENERATING') {
        return 2000; // 每 2 秒轮询
      }
      return false;
    },
  });
}

/**
 * 生成报告 Mutation
 */
export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, type }: { caseId: string; type: string }) => generateReport(caseId, type),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['reports', caseId] });
    },
  });
}

/**
 * 取消报告生成 Mutation
 */
export function useCancelReport() {
  return useMutation({
    mutationFn: cancelReport,
  });
}

/**
 * 删除报告 Mutation
 */
export function useDeleteReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });
}

/**
 * 重新生成报告 Mutation
 */
export function useRegenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: regenerateReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });
}
