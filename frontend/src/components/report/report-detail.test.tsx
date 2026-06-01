import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ReportDetail } from './report-detail';
import * as reportHooks from '@/hooks/use-report';
import * as reportPrintHooks from '@/hooks/use-report-print';
import type { ReportDetail as ReportDetailType } from '@/types/report.types';

const mockReport: ReportDetailType = {
  id: 'report-1',
  case_id: 1,
  report_type: 'ANALYSIS',
  report_type_name: '案件分析',
  report_type_icon: 'file-text',
  title: '案件分析报告',
  description: '测试报告',
  status: 'COMPLETED',
  progress: { total: 1, completed: 1, failed: 0, progress: 100, status: 'COMPLETED' },
  total_tokens: 100,
  processing_time: 2,
  version: 1,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
  completed_at: '2026-06-01T00:01:00Z',
  total_sections: 1,
  completed_sections: 1,
  sections: [
    {
      id: 'section-1',
      outline_id: 'report-1',
      section_index: 1,
      title: '事实摘要',
      content: '基于现有证据整理。',
      key_points: [],
      status: 'completed',
      created_at: '2026-06-01T00:00:00Z',
      completed_at: '2026-06-01T00:01:00Z',
    },
  ],
};

describe('ReportDetail', () => {
  it('labels report export and print surfaces as reviewable workpapers', () => {
    vi.spyOn(reportHooks, 'useReportDetail').mockReturnValue({
      data: mockReport,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof reportHooks.useReportDetail>);
    vi.spyOn(reportHooks, 'useRegenerateReport').mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof reportHooks.useRegenerateReport>);
    vi.spyOn(reportPrintHooks, 'useReportPrint').mockReturnValue({
      printCurrentPage: vi.fn(),
      printElement: vi.fn(),
      printReport: vi.fn(),
      printSection: vi.fn(),
    });

    render(<ReportDetail reportId="report-1" onBack={vi.fn()} />);

    expect(screen.getByText('AI 法律工作底稿')).toBeInTheDocument();
    expect(screen.getByText(/导出、打印、提交或对外发送前/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /导出工作底稿/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /打印工作底稿/ })).toBeInTheDocument();
  });
});
