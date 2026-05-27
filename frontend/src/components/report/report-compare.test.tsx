import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ReportCompare } from './report-compare';
import type { ReportOutline } from '@/types/report.types';

// Mock console.error
const originalError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});
afterEach(() => {
  console.error = originalError;
});

describe('ReportCompare', () => {
  // Mock data factory
  const createMockReports = (reports: Partial<ReportOutline>[]) =>
    reports.map((r, i) => ({
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
    }));

  it('renders compare view with report selection', () => {
    render(<ReportCompare reports={createMockReports([
      { id: '1', title: '报告1' },
      { id: '2', title: '报告2' },
    ])} onBack={vi.fn()} />);

    expect(screen.getByText('选择要对比的报告')).toBeInTheDocument();
    expect(screen.getByText('开始对比')).toBeInTheDocument();
  });

  it('shows back button', () => {
    const onBack = vi.fn();
    render(<ReportCompare reports={createMockReports([
      { id: '1', title: '报告1' },
      { id: '2', title: '报告2' },
    ])} onBack={onBack} />);

    const backButton = screen.getByText('返回');
    expect(backButton).toBeInTheDocument();
  });

  it('has compare button disabled when no reports selected', () => {
    render(<ReportCompare reports={createMockReports([
      { id: '1', title: '报告1' },
      { id: '2', title: '报告2' },
    ])} onBack={vi.fn()} />);

    const compareButton = screen.getByText('开始对比');
    expect(compareButton).toBeDisabled();
  });
});
