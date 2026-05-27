import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { ReminderCard } from './reminder-card';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

vi.mock('@/lib/date', () => ({
  formatChineseDate: (date: string) => date,
}));

describe('ReminderCard', () => {
  it('renders reminder information', () => {
    render(
      <ReminderCard
        title="Evidence deadline approaching"
        caseTitle="Loan Dispute Case"
        type="deadline"
        dueDate="2024-04-15"
        isRead={false}
        priority="high"
        onClick={vi.fn()}
        onMarkRead={vi.fn()}
      />
    );

    expect(screen.getByText('Evidence deadline approaching')).toBeInTheDocument();
    expect(screen.getByText('Loan Dispute Case')).toBeInTheDocument();
    expect(screen.getByText(/2024-04-15/)).toBeInTheDocument();
  });

  it('shows high priority with color', () => {
    render(
      <ReminderCard
        title="Urgent reminder"
        caseTitle="Test Case"
        type="deadline"
        isRead={false}
        priority="high"
        onClick={vi.fn()}
        onMarkRead={vi.fn()}
      />
    );

    const card = document.querySelector('[class*="border-l-red-500"]');
    expect(card).toBeInTheDocument();
  });

  it('shows medium priority with color', () => {
    render(
      <ReminderCard
        title="Medium reminder"
        caseTitle="Test Case"
        type="deadline"
        isRead={false}
        priority="medium"
        onClick={vi.fn()}
        onMarkRead={vi.fn()}
      />
    );

    const card = document.querySelector('[class*="border-l-amber-500"]');
    expect(card).toBeInTheDocument();
  });

  it('calls onMarkRead when mark as read button is clicked', () => {
    const onMarkRead = vi.fn();
    render(
      <ReminderCard
        title="Unread reminder"
        caseTitle="Test Case"
        type="deadline"
        isRead={false}
        priority="low"
        onClick={vi.fn()}
        onMarkRead={onMarkRead}
      />
    );

    fireEvent.click(screen.getByText('标记已读'));
    expect(onMarkRead).toHaveBeenCalledTimes(1);
  });

  it('calls onClick when view button is clicked', () => {
    const onClick = vi.fn();
    render(
      <ReminderCard
        title="Test reminder"
        caseTitle="Test Case"
        type="deadline"
        isRead={false}
        priority="high"
        onClick={onClick}
        onMarkRead={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('查看'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
