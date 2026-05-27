import * as dashboardApi from '@/api/dashboard.api';
import { CaseOverview } from '@/components/dashboard/case-overview';
import { render, screen } from '@/test/test-utils';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/api/dashboard.api');
vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button' },
}));

describe('CaseOverview', () => {
  it('renders case statistics correctly', () => {
    vi.mocked(dashboardApi.useDashboard).mockReturnValue({
      data: {
        caseStats: { total: 42, inProgress: 15, newThisMonth: 8, inExecution: 3 },
        urgentTasks: [],
        upcomingTasks: [],
        todaySuggestions: [],
      },
      isLoading: false,
      isError: false,
    } as never);

    render(<CaseOverview />);

    expect(screen.getByText('全案件数')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('进行中')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('本月新增')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('执行中')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading is true', () => {
    vi.mocked(dashboardApi.useDashboard).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as never);

    render(<CaseOverview />);

    expect(screen.queryByText('全案件数')).not.toBeInTheDocument();
  });

  it('shows fallback stats when isError is true', () => {
    vi.mocked(dashboardApi.useDashboard).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as never);

    render(<CaseOverview />);

    expect(screen.getByText('全案件数')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('shows empty state when no stats available', () => {
    vi.mocked(dashboardApi.useDashboard).mockReturnValue({
      data: { caseStats: null },
      isLoading: false,
      isError: false,
    } as never);

    render(<CaseOverview />);

    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('displays zero counts when stats are empty', () => {
    vi.mocked(dashboardApi.useDashboard).mockReturnValue({
      data: {
        caseStats: { total: 0, inProgress: 0, newThisMonth: 0, inExecution: 0 },
        urgentTasks: [],
        upcomingTasks: [],
        todaySuggestions: [],
      },
      isLoading: false,
      isError: false,
    } as never);

    render(<CaseOverview />);

    const zeros = screen.getAllByText('0');
    expect(zeros.length).toBeGreaterThanOrEqual(4);
  });

  it('renders the grid container', () => {
    vi.mocked(dashboardApi.useDashboard).mockReturnValue({
      data: {
        caseStats: { total: 1, inProgress: 1, newThisMonth: 1, inExecution: 1 },
        urgentTasks: [],
        upcomingTasks: [],
        todaySuggestions: [],
      },
      isLoading: false,
      isError: false,
    } as never);

    const { container } = render(<CaseOverview />);
    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
  });
});
