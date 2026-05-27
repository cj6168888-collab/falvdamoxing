import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { TOKEN_STORAGE_KEY } from '@/lib/api-config';
import type { ReportOutline, ReportDetail, ReportSection } from '@/types/report.types';

// 导出类型供其他模块使用
export type { ReportOutline, ReportDetail, ReportSection };

/**
 * 获取案件报告列表
 * @param caseId 案件ID
 */
export function useReports(caseId: string) {
  return useQuery({
    queryKey: ['reports', caseId],
    queryFn: () => axiosInstance.get<{ reports: ReportOutline[]; total: number }>(`/api/reports/list/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

/**
 * 获取报告列表（用于 hooks）
 */
export function useReportList(caseId: string) {
  return useReports(caseId);
}

/**
 * 获取报告详情
 * @param reportId 报告ID
 */
export function useReportDetail(reportId: string) {
  return useQuery({
    queryKey: ['report-detail', reportId],
    queryFn: () => axiosInstance.get<ReportDetail>(`/api/reports/detail/${reportId}`).then(res => res.data),
    enabled: !!reportId,
  });
}

/**
 * 生成报告
 * @param caseId 案件ID
 * @param type 报告类型
 */
export async function generateReport(caseId: string, type: string) {
  return axiosInstance.post(`/api/reports/generate/${caseId}`, { report_type: type }).then(res => res.data);
}

/**
 * 取消报告生成
 * @param caseId 案件ID
 */
export async function cancelReport(caseId: string) {
  return axiosInstance.post(`/api/reports/cancel/${caseId}`);
}

/**
 * 快速分析
 * @param caseId 案件ID
 */
export async function quickAnalysis(caseId: string) {
  return axiosInstance.post(`/api/reports/quick-analysis/${caseId}`).then(res => res.data);
}

/**
 * 删除报告
 * @param reportId 报告ID
 */
export async function deleteReport(reportId: string) {
  return axiosInstance.delete(`/api/reports/${reportId}`).then(res => res.data);
}

/**
 * 重新生成报告
 * @param reportId 报告ID
 */
export async function regenerateReport(reportId: string) {
  return axiosInstance.post(`/api/reports/regenerate/${reportId}`).then(res => res.data);
}

/**
 * 获取报告生成状态
 * @param caseId 案件ID
 * @param reportType 报告类型
 */
export async function getReportStatus(caseId: string, reportType: string = 'analysis') {
  return axiosInstance.get(`/api/reports/status/${caseId}`, {
    params: { report_type: reportType }
  }).then(res => res.data);
}

/**
 * 失效报告缓存
 * @param caseId 案件ID
 */
export async function invalidateReportCache(caseId: string) {
  return axiosInstance.post(`/api/reports/invalidate-cache/${caseId}`).then(res => res.data);
}

/**
 * 获取文书清单报告
 * @param caseId 案件ID
 */
export async function getDocumentsReport(caseId: string) {
  return axiosInstance.post(`/api/reports/generate-documents/${caseId}`).then(res => res.data);
}

/**
 * 导出报告
 * @param reportId 报告ID
 * @param format 导出格式：markdown, text, pdf, word
 */
export async function exportReport(
  reportId: string,
  format: 'markdown' | 'text' | 'pdf' | 'word' = 'markdown'
) {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY) || '';
  const response = await fetch(`/api/reports/export/${reportId}?format=${format}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('导出失败');
  const blob = await response.blob();

  // 获取文件扩展名
  const ext = format === 'markdown' ? 'md'
    : format === 'text' ? 'txt'
    : format === 'pdf' ? 'pdf'
    : 'docx';

  // 从 Content-Disposition 获取文件名
  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = `report.${ext}`;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match) {
      filename = match[1].replace(/['"]/g, '');
    }
  }
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/**
 * 报告对比结果类型
 */
export interface ReportCompareResult {
  report_1: {
    id: string;
    title: string;
    report_type: string;
    version: number;
    created_at: string | null;
    sections_count: number;
  };
  report_2: {
    id: string;
    title: string;
    report_type: string;
    version: number;
    created_at: string | null;
    sections_count: number;
  };
  section_comparison: Array<{
    index: number;
    status: 'both' | 'only_first' | 'only_second';
    section_1?: {
      title: string;
      content_length: number;
      completed_at: string | null;
    };
    section_2?: {
      title: string;
      content_length: number;
      completed_at: string | null;
    };
    similarity: number | null;
  }>;
  summary: {
    total_sections: number;
    common_sections: number;
    only_in_first: number;
    only_in_second: number;
  };
}

/**
 * 对比两个报告
 * @param reportId1 第一个报告ID
 * @param reportId2 第二个报告ID
 */
export async function compareReports(reportId1: string, reportId2: string): Promise<ReportCompareResult> {
  return axiosInstance.get<ReportCompareResult>(
    `/api/reports/compare/${reportId1}/${reportId2}`
  ).then(res => res.data);
}

export interface ReportCompleteEvent {
  report_id?: string;
  title?: string;
  report_type?: string;
  total_sections?: number;
  completed_sections?: number;
  created_at?: string;
}

/**
 * 监听报告生成进度（SSE 流式）
 * @param caseId 案件ID
 * @param reportType 报告类型
 * @param onProgress 进度回调
 * @param onSectionStart 章节开始回调
 * @param onSectionContent 章节内容回调
 * @param onComplete 完成回调
 * @param onError 错误回调
 */
export function subscribeToReportProgress(
  caseId: string,
  reportType: string,
  callbacks: {
    onProgress?: (data: { progress: number; message: string }) => void;
    onSectionStart?: (data: { section_index: number; title: string; content: string }) => void;
    onSectionContent?: (data: { section_index: number; title: string; content: string }) => void;
    onSectionError?: (data: { section_index: number; title: string; error: string }) => void;
    onComplete?: (data: ReportCompleteEvent) => void;
    onError?: (error: string) => void;
  }
): () => void {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY) || '';
  const eventSource = new EventSource(
    `/api/reports/generate-stream/${caseId}?report_type=${reportType}`,
    {
      headers: { Authorization: `Bearer ${token}` }
    } as EventSourceInit & { headers: Record<string, string> }
  );

  eventSource.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onProgress?.(data);
    } catch (e) {
      console.error('Failed to parse progress event:', e);
    }
  });

  eventSource.addEventListener('section_start', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onSectionStart?.(data);
    } catch (e) {
      console.error('Failed to parse section_start event:', e);
    }
  });

  eventSource.addEventListener('section_content', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onSectionContent?.(data);
    } catch (e) {
      console.error('Failed to parse section_content event:', e);
    }
  });

  eventSource.addEventListener('section_error', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onSectionError?.(data);
    } catch (e) {
      console.error('Failed to parse section_error event:', e);
    }
  });

  eventSource.addEventListener('complete', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onComplete?.(data);
      eventSource.close();
    } catch (e) {
      console.error('Failed to parse complete event:', e);
    }
  });

  eventSource.addEventListener('error', (event) => {
    console.error('SSE error:', event);
    callbacks.onError?.('连接错误');
    eventSource.close();
  });

  // 返回关闭函数
  return () => {
    eventSource.close();
  };
}
