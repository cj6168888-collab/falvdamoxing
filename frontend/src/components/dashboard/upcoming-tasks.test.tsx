import { UpcomingTasks } from '@/components/dashboard/upcoming-tasks';
import { render, screen } from '@/test/test-utils';
import type { UpcomingTask } from '@/types/dashboard.types';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('framer-motion', () => ({
  motion: {
    div: ({
      whileHover: _whileHover,
      whileTap: _whileTap,
      transition: _transition,
      ...props
    }: Record<string, unknown>) => <div {...(props as JSX.IntrinsicElements['div'])} />,
    button: ({
      whileHover: _whileHover,
      whileTap: _whileTap,
      transition: _transition,
      ...props
    }: Record<string, unknown>) => <button {...(props as JSX.IntrinsicElements['button'])} />,
  },
}));

const mockTasks: UpcomingTask[] = [
  {
    id: 'task-1',
    caseId: 'case-1',
    caseTitle: 'Loan Dispute',
    type: 'hearing',
    title: 'First Hearing',
    daysRemaining: 15,
    dueDate: '2024-04-15',
    redirectPath: '/cases/case-1/hearings',
  },
  {
    id: 'task-2',
    caseId: 'case-2',
    caseTitle: 'Contract Case',
    type: 'filing',
    title: 'File Documents',
    daysRemaining: 25,
    dueDate: '2024-04-25',
    redirectPath: '/cases/case-2/documents',
  },
];

beforeEach(() => {
  mockNavigate.mockClear();
});

describe('UpcomingTasks', () => {
  it('renders upcoming tasks list with correct data', () => {
    render(
      <UpcomingTasks
        tasks={mockTasks}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('近期待办')).toBeInTheDocument();
    expect(screen.getByText('First Hearing')).toBeInTheDocument();
    expect(screen.getByText('File Documents')).toBeInTheDocument();
    expect(screen.getByText('Loan Dispute')).toBeInTheDocument();
    expect(screen.getByText('Contract Case')).toBeInTheDocument();
  });

  it('shows empty state when no tasks', () => {
    render(
      <UpcomingTasks
        tasks={[]}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('暂无近期待办')).toBeInTheDocument();
    expect(
      screen.getByText('30 天内没有待办事项，好好休息或处理其他工作'),
    ).toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading is true', () => {
    render(
      <UpcomingTasks
        tasks={[]}
        isLoading={true}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('近期待办')).toBeInTheDocument();
    expect(screen.getByText('30 天内')).toBeInTheDocument();
  });

  it('navigates to correct path when task is clicked', async () => {
    const user = userEvent.setup();
    render(
      <UpcomingTasks
        tasks={mockTasks}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    const taskButtons = screen.getAllByRole('button');
    await user.click(taskButtons[0]);

    expect(mockNavigate).toHaveBeenCalledWith('/cases/case-1/hearings');
  });

  it('shows error state with retry button', () => {
    const handleRetry = vi.fn();
    render(
      <UpcomingTasks
        tasks={[]}
        isLoading={false}
        isError={true}
        onRetry={handleRetry}
      />,
    );

    expect(screen.getByText('加载近期待办失败')).toBeInTheDocument();
    const retryButton = screen.getByText('点击重试');
    expect(retryButton).toBeInTheDocument();
  });
});
