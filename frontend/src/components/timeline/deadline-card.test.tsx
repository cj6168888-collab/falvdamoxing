import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { DeadlineCard } from '@/components/timeline/deadline-card';

vi.mock('@/components/common/deadline-countdown', () => ({
  DeadlineCountdown: ({ dueDate, daysRemaining }: { dueDate: string; daysRemaining: number }) => (
    <div data-testid="deadline-countdown">
      <span>{dueDate}</span>
      <span>{daysRemaining}天</span>
    </div>
  ),
}));

describe('DeadlineCard', () => {
  it('renders deadline info correctly', () => {
    render(
      <DeadlineCard
        title="举证期限"
        dueDate="2024-04-15"
        daysRemaining={10}
      />,
    );

    expect(screen.getByText('举证期限')).toBeInTheDocument();
    expect(screen.getByText('2024-04-15')).toBeInTheDocument();
    expect(screen.getByText('10天')).toBeInTheDocument();
  });

  it('shows legal basis when provided', () => {
    render(
      <DeadlineCard
        title="举证期限"
        dueDate="2024-04-15"
        daysRemaining={10}
        legalBasis="《民事诉讼法》第65条"
      />,
    );

    expect(screen.getByText('《民事诉讼法》第65条')).toBeInTheDocument();
  });

  it('does not show legal basis when not provided', () => {
    render(
      <DeadlineCard
        title="举证期限"
        dueDate="2024-04-15"
        daysRemaining={10}
      />,
    );

    expect(screen.queryByText('《民事诉讼法》第65条')).not.toBeInTheDocument();
  });

  it('shows overdue state with negative days', () => {
    render(
      <DeadlineCard
        title="答辩期限"
        dueDate="2024-01-15"
        daysRemaining={-5}
      />,
    );

    expect(screen.getByText('答辩期限')).toBeInTheDocument();
    expect(screen.getByText('-5天')).toBeInTheDocument();
  });

  it('renders countdown component with correct props', () => {
    render(
      <DeadlineCard
        title="上诉期限"
        dueDate="2024-06-01"
        daysRemaining={30}
      />,
    );

    expect(screen.getByTestId('deadline-countdown')).toBeInTheDocument();
  });
});
