import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ReportList } from './report-list';
import * as reportHooks from '@/hooks/use-report';
import type { ReportOutline } from '@/types/report.types';

// Mock console.error to suppress React warnings
const originalError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});
afterEach(() => {
  console.error = originalError;
});

describe('ReportList', () => {
  type UseReportListResult = ReturnType<typeof reportHooks.useReportList>;

  // Mock data factory
  const createMockReports = (reports: Partial<ReportOutline>[]): UseReportListResult => ({
    data: {
      reports: reports.map((r, i) => ({
        id: r.id || `report-${i}`,
        case_id: r.case_id || 1,
        report_type: r.report_type || 'ANALYSIS',
        report_type_name: r.report_type_name || '案件分析',
        title: r.title || '测试报告',
        description: r.description || '',
        status: r.status || 'COMPLETED',
        progress: r.progress || { total: 5, completed: 5, failed: 0, progress: 100, status: 'COMPLETED' },
        version: r.version || 1,
        created_at: r.created_at || new Date().toISOString(),
        updated_at: r.updated_at || new Date().toISOString(),
        completed_at: r.completed_at || null,
      }))
    },
    isLoading: false,
    refetch: vi.fn(),
  });

  it('renders report list correctly', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue(createMockReports([
      { id: '1', title: '案件分析报告', report_type: 'ANALYSIS', status: 'COMPLETED' },
      { id: '2', title: '策略建议报告', report_type: 'STRATEGY', status: 'COMPLETED' },
    ]));

    render(<ReportList caseId="1" />);

    expect(screen.getByText('案件分析报告')).toBeInTheDocument();
    expect(screen.getByText('策略建议报告')).toBeInTheDocument();
  });

  it('shows report status badges', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue(createMockReports([
      { id: '1', title: '生成中报告', status: 'GENERATING' },
      { id: '2', title: '已完成报告', status: 'COMPLETED' },
      { id: '3', title: '失败报告', status: 'FAILED' },
    ]));

    render(<ReportList caseId="1" />);

    expect(screen.getByText('生成中')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('失败')).toBeInTheDocument();
  });

  it('shows empty state when no reports', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue({
      data: { reports: [] },
      isLoading: false,
      refetch: vi.fn(),
    } as UseReportListResult);

    render(<ReportList caseId="1" />);

    expect(screen.getByText('暂无报告')).toBeInTheDocument();
    expect(screen.getByText('生成第一份报告')).toBeInTheDocument();
  });

  it('shows generate report button', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue({
      data: { reports: [] },
      isLoading: false,
      refetch: vi.fn(),
    } as UseReportListResult);

    render(<ReportList caseId="1" />);

    expect(screen.getByText('生成报告')).toBeInTheDocument();
  });

  it('shows loading skeleton', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue({
      data: undefined,
      isLoading: true,
      refetch: vi.fn(),
    } as UseReportListResult);

    render(<ReportList caseId="1" />);

    // Should not show empty state when loading
    expect(screen.queryByText('暂无报告')).not.toBeInTheDocument();
  });

  it('shows version badge for non-first versions', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue(createMockReports([
      { id: '1', title: 'V1 报告', version: 1 },
      { id: '2', title: 'V2 报告', version: 2 },
    ]));

    render(<ReportList caseId="1" />);

    expect(screen.getAllByText(/V2/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/^V1$/)).not.toBeInTheDocument();
  });

  it('shows compare button when multiple reports exist', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue(createMockReports([
      { id: '1', title: '报告1' },
      { id: '2', title: '报告2' },
    ]));

    render(<ReportList caseId="1" />);

    expect(screen.getByText('对比报告')).toBeInTheDocument();
  });

  it('hides compare button when only one report exists', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue(createMockReports([
      { id: '1', title: '唯一报告' },
    ]));

    render(<ReportList caseId="1" />);

    expect(screen.queryByText('对比报告')).not.toBeInTheDocument();
  });

  it('shows progress bar for generating reports', () => {
    vi.spyOn(reportHooks, 'useReportList').mockReturnValue(createMockReports([
      { id: '1', title: '生成中报告', status: 'GENERATING', progress: { total: 5, completed: 2, failed: 0, progress: 40, status: 'GENERATING' } },
    ]));

    render(<ReportList caseId="1" />);

    expect(screen.getByText('40% 完成')).toBeInTheDocument();
  });
});
