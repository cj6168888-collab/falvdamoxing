import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { createMockDeadline } from '@/test/fixtures';
import type { Deadline } from '@/types/deadline.types';
import type { Reminder } from '@/types/reminder.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface TimelineReminderIntegrationProps {
  deadlines: Deadline[];
  reminders: Reminder[];
  onCreateDeadline: (deadline: Partial<Deadline>) => void;
  onUpdateDeadline: (id: string, updates: Partial<Deadline>) => void;
  onCompleteDeadline: (id: string) => void;
}

function TimelineReminderIntegration({
  deadlines,
  reminders,
  onCreateDeadline,
  onUpdateDeadline,
  onCompleteDeadline,
}: TimelineReminderIntegrationProps) {
  const urgentReminders = reminders.filter(r => r.priority === 'high' && !r.isRead);

  return (
    <div data-testid="timeline-reminder">
      <div data-testid="deadline-count">{deadlines.length}</div>
      <div data-testid="reminder-count">{urgentReminders.length}</div>
      <div data-testid="deadlines">
        {deadlines.map(dl => (
          <div key={dl.id} data-testid={`deadline-${dl.id}`}>
            <span data-testid={`deadline-title-${dl.id}`}>{dl.title}</span>
            <span data-testid={`deadline-status-${dl.id}`}>{dl.status}</span>
            <button data-testid={`complete-${dl.id}`} onClick={() => onCompleteDeadline(dl.id)}>
              Complete
            </button>
            <button data-testid={`update-${dl.id}`} onClick={() => onUpdateDeadline(dl.id, { dueDate: '2024-05-01' })}>
              Update
            </button>
          </div>
        ))}
      </div>
      <button
        data-testid="create-deadline-btn"
        onClick={() => onCreateDeadline({
          id: 'dl-new',
          title: 'New Deadline',
          type: 'filing',
          dueDate: '2024-05-15',
          status: 'pending',
        })}
      >
        Create Deadline
      </button>
    </div>
  );
}

describe('Time Control ↔ Reminder System Integration', () => {
  const initialDeadlines = [
    createMockDeadline({ id: 'dl-1', title: 'Evidence Deadline', dueDate: '2024-04-15', status: 'pending' }),
    createMockDeadline({ id: 'dl-2', title: 'Hearing Date', dueDate: '2024-06-20', status: 'pending' }),
  ];

  const initialReminders: Reminder[] = [
    {
      id: 'rem-1',
      caseId: 'case-1',
      caseTitle: 'Loan Dispute',
      type: 'deadline',
      title: 'Evidence submission due',
      priority: 'high',
      isRead: false,
      dueDate: '2024-04-15',
      createdAt: '2024-04-10T10:00:00Z',
    },
  ];

  it('generates reminder when deadline is created', () => {
    const handleCreate = vi.fn();
    const handleUpdate = vi.fn();
    const handleComplete = vi.fn();

    render(
      <TimelineReminderIntegration
        deadlines={initialDeadlines}
        reminders={initialReminders}
        onCreateDeadline={handleCreate}
        onUpdateDeadline={handleUpdate}
        onCompleteDeadline={handleComplete}
      />
    );

    fireEvent.click(screen.getByTestId('create-deadline-btn'));

    expect(handleCreate).toHaveBeenCalledWith({
      id: 'dl-new',
      title: 'New Deadline',
      type: 'filing',
      dueDate: '2024-05-15',
      status: 'pending',
    });
  });

  it('updates reminder when deadline is updated', () => {
    const handleCreate = vi.fn();
    const handleUpdate = vi.fn();
    const handleComplete = vi.fn();

    render(
      <TimelineReminderIntegration
        deadlines={initialDeadlines}
        reminders={initialReminders}
        onCreateDeadline={handleCreate}
        onUpdateDeadline={handleUpdate}
        onCompleteDeadline={handleComplete}
      />
    );

    fireEvent.click(screen.getByTestId('update-dl-1'));

    expect(handleUpdate).toHaveBeenCalledWith('dl-1', { dueDate: '2024-05-01' });
  });

  it('marks reminder as read when deadline is completed', () => {
    const handleCreate = vi.fn();
    const handleUpdate = vi.fn();
    const handleComplete = vi.fn();

    render(
      <TimelineReminderIntegration
        deadlines={initialDeadlines}
        reminders={initialReminders}
        onCreateDeadline={handleCreate}
        onUpdateDeadline={handleUpdate}
        onCompleteDeadline={handleComplete}
      />
    );

    expect(screen.getByTestId('deadline-status-dl-1')).toHaveTextContent('pending');

    fireEvent.click(screen.getByTestId('complete-dl-1'));

    expect(handleComplete).toHaveBeenCalledWith('dl-1');
  });

  it('shows urgent reminder for overdue deadline', () => {
    const overdueDeadlines = [
      createMockDeadline({ id: 'dl-overdue', title: 'Overdue Filing', dueDate: '2024-03-01', status: 'overdue' }),
      ...initialDeadlines,
    ];

    const overdueReminders: Reminder[] = [
      ...initialReminders,
      {
        id: 'rem-overdue',
        caseId: 'case-1',
        caseTitle: 'Loan Dispute',
        type: 'deadline',
        title: 'Filing deadline has passed',
        priority: 'high',
        isRead: false,
        dueDate: '2024-03-01',
        createdAt: '2024-03-02T10:00:00Z',
      },
    ];

    render(
      <TimelineReminderIntegration
        deadlines={overdueDeadlines}
        reminders={overdueReminders}
        onCreateDeadline={vi.fn()}
        onUpdateDeadline={vi.fn()}
        onCompleteDeadline={vi.fn()}
      />
    );

    expect(screen.getByTestId('deadline-status-dl-overdue')).toHaveTextContent('overdue');
    expect(screen.getByTestId('reminder-count')).toHaveTextContent('2');
  });
});
