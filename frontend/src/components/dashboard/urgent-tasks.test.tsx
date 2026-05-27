import { UrgentTasks } from '@/components/dashboard/urgent-tasks';
import { render, screen } from '@/test/test-utils';
import type { UrgentTask } from '@/types/dashboard.types';
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
    span: ({
      whileHover: _whileHover,
      whileTap: _whileTap,
      transition: _transition,
      ...props
    }: Record<string, unknown>) => <span {...(props as JSX.IntrinsicElements['span'])} />,
  },
}));

const mockTasks: UrgentTask[] = [
  {
    id: 'task-1',
    caseId: 'case-1',
    caseTitle: 'Loan Dispute',
    type: 'appeal',
    title: 'Appeal Deadline',
    description: 'File appeal within 15 days',
    daysRemaining: -2,
    dueDate: '2024-03-01',
    redirectPath: '/cases/case-1/appeals',
  },
  {
    id: 'task-2',
    caseId: 'case-2',
    caseTitle: 'Contract Dispute',
    type: 'evidence',
    title: 'Evidence Submission',
    description: 'Submit evidence by deadline',
    daysRemaining: 2,
    dueDate: '2024-03-15',
    redirectPath: '/cases/case-2/evidence',
  },
  {
    id: 'task-3',
    caseId: 'case-3',
    caseTitle: 'Property Case',
    type: 'hearing',
    title: 'Court Hearing',
    description: 'Attend court hearing',
    daysRemaining: 5,
    dueDate: '2024-03-20',
    redirectPath: '/cases/case-3/hearings',
  },
];

beforeEach(() => {
  mockNavigate.mockClear();
});

describe('UrgentTasks', () => {
  it('renders urgent tasks list with correct data', () => {
    render(
      <UrgentTasks
        tasks={mockTasks}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('紧急待办')).toBeInTheDocument();
    expect(screen.getByText('Appeal Deadline')).toBeInTheDocument();
    expect(screen.getByText('Evidence Submission')).toBeInTheDocument();
    expect(screen.getByText('Court Hearing')).toBeInTheDocument();
    expect(screen.getByText('Loan Dispute')).toBeInTheDocument();
    expect(screen.getByText('Contract Dispute')).toBeInTheDocument();
  });

  it('shows empty state when no urgent tasks', () => {
    render(
      <UrgentTasks
        tasks={[]}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('暂无紧急事项')).toBeInTheDocument();
    expect(
      screen.getByText('当前没有需要立即处理的事项，继续保持关注'),
    ).toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading is true', () => {
    render(
      <UrgentTasks
        tasks={[]}
        isLoading={true}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('紧急待办')).toBeInTheDocument();
    expect(screen.getByText('需要立即行动')).toBeInTheDocument();
  });

  it('navigates to correct path when task is clicked', async () => {
    const user = userEvent.setup();
    render(
      <UrgentTasks
        tasks={mockTasks}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    const taskButtons = screen.getAllByRole('button');
    await user.click(taskButtons[0]);

    expect(mockNavigate).toHaveBeenCalledWith('/cases/case-1/appeals');
  });

  it('shows error state with retry button', () => {
    const handleRetry = vi.fn();
    render(
      <UrgentTasks
        tasks={[]}
        isLoading={false}
        isError={true}
        onRetry={handleRetry}
      />,
    );

    expect(screen.getByText('加载紧急待办失败')).toBeInTheDocument();
    const retryButton = screen.getByText('点击重试');
    expect(retryButton).toBeInTheDocument();
  });
});
