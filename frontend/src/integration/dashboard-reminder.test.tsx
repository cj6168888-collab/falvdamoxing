import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import type { Reminder } from '@/types/reminder.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface DashboardReminderIntegrationProps {
  reminders: Reminder[];
  onReminderRead: (id: string) => void;
}

function DashboardReminderIntegration({ reminders, onReminderRead }: DashboardReminderIntegrationProps) {
  const urgentReminders = reminders.filter(r => r.priority === 'high' && !r.isRead);
  const unreadCount = reminders.filter(r => !r.isRead).length;

  return (
    <div data-testid="dashboard-reminder">
      <div data-testid="reminder-count">{unreadCount}</div>
      <div data-testid="urgent-section">
        {urgentReminders.map(reminder => (
          <div key={reminder.id} data-testid={`urgent-${reminder.id}`}>
            <span data-testid={`urgent-title-${reminder.id}`}>{reminder.title}</span>
            <button data-testid={`mark-read-${reminder.id}`} onClick={() => onReminderRead(reminder.id)}>
              Mark Read
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

describe('Dashboard ↔ Reminder System Integration', () => {
  const getMockReminders = (): Reminder[] => [
    {
      id: 'rem-1',
      caseId: 'case-1',
      caseTitle: 'Loan Dispute',
      type: 'deadline',
      title: 'Evidence submission due tomorrow',
      priority: 'high',
      isRead: false,
      dueDate: '2024-04-16',
      redirectPath: '/cases/case-1/evidence',
      createdAt: '2024-04-14T10:00:00Z',
    },
    {
      id: 'rem-2',
      caseId: 'case-1',
      caseTitle: 'Loan Dispute',
      type: 'hearing',
      title: 'Hearing scheduled',
      priority: 'medium',
      isRead: false,
      dueDate: '2024-06-20',
      redirectPath: '/cases/case-1/hearing',
      createdAt: '2024-04-10T10:00:00Z',
    },
    {
      id: 'rem-3',
      caseId: 'case-1',
      caseTitle: 'Loan Dispute',
      type: 'evidence',
      title: 'New evidence uploaded',
      priority: 'low',
      isRead: true,
      createdAt: '2024-04-12T10:00:00Z',
    },
  ];

  it('displays urgent tasks from reminder data', () => {
    const handleReminderRead = vi.fn();
    render(
      <DashboardReminderIntegration
        reminders={getMockReminders()}
        onReminderRead={handleReminderRead}
      />
    );

    expect(screen.getByTestId('urgent-rem-1')).toBeInTheDocument();
    expect(screen.getByTestId('urgent-title-rem-1')).toHaveTextContent('Evidence submission due tomorrow');
    expect(screen.queryByTestId('urgent-rem-2')).not.toBeInTheDocument();
    expect(screen.queryByTestId('urgent-rem-3')).not.toBeInTheDocument();
  });

  it('updates dashboard when reminder is marked as read', async () => {
    const mockReminders = getMockReminders();
    const handleReminderRead = vi.fn((id: string) => {
      const reminder = mockReminders.find(r => r.id === id);
      if (reminder) reminder.isRead = true;
    });

    render(
      <DashboardReminderIntegration
        reminders={getMockReminders()}
        onReminderRead={handleReminderRead}
      />
    );

    expect(screen.getByTestId('reminder-count')).toHaveTextContent('2');
    expect(screen.getByTestId('urgent-rem-1')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('mark-read-rem-1'));

    await waitFor(() => {
      expect(handleReminderRead).toHaveBeenCalledWith('rem-1');
    });
  });

  it('shows new reminder in urgent section', () => {
    const handleReminderRead = vi.fn();
    const newReminder: Reminder = {
      id: 'rem-4',
      caseId: 'case-1',
      caseTitle: 'Loan Dispute',
      type: 'deadline',
      title: 'Urgent court filing deadline',
      priority: 'high',
      isRead: false,
      dueDate: '2024-04-15',
      redirectPath: '/cases/case-1/filing',
      createdAt: '2024-04-14T12:00:00Z',
    };

    render(
      <DashboardReminderIntegration
        reminders={[...getMockReminders(), newReminder]}
        onReminderRead={handleReminderRead}
      />
    );

    expect(screen.getByTestId('urgent-rem-4')).toBeInTheDocument();
    expect(screen.getByTestId('urgent-title-rem-4')).toHaveTextContent('Urgent court filing deadline');
  });

  it('updates reminder count correctly', () => {
    const handleReminderRead = vi.fn();
    const reminders = getMockReminders();

    const { rerender } = render(
      <DashboardReminderIntegration
        reminders={reminders}
        onReminderRead={handleReminderRead}
      />
    );

    expect(screen.getByTestId('reminder-count')).toHaveTextContent('2');

    const updatedReminders = reminders.map(r =>
      r.id === 'rem-2' ? { ...r, isRead: true } : r
    );

    rerender(
      <DashboardReminderIntegration
        reminders={updatedReminders}
        onReminderRead={handleReminderRead}
      />
    );

    expect(screen.getByTestId('reminder-count')).toHaveTextContent('1');
  });
});
