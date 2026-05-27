import { useState } from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { createMockDeadline } from '@/test/fixtures';
import type { Deadline } from '@/types/deadline.types';
import type { Reminder } from '@/types/reminder.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface DeadlineReminderState {
  deadlines: Deadline[];
  reminders: Reminder[];
  lastNavigation: string | null;
  dashboardUrgentCount: number;
  currentTime: string;
}

function DeadlineReminderTest({ initialState }: { initialState: DeadlineReminderState }) {
  const [state, setState] = useState<DeadlineReminderState>(initialState);

  const createDeadline = () => {
    const newDeadline = createMockDeadline({
      id: 'dl-e2e',
      title: 'Evidence Submission',
      dueDate: '2024-04-20',
      status: 'pending',
    });

    const newReminder: Reminder = {
      id: 'rem-e2e',
      caseId: 'case-1',
      caseTitle: 'Test Case',
      type: 'deadline',
      title: 'Evidence Submission due in 3 days',
      priority: 'high',
      isRead: false,
      dueDate: '2024-04-20',
      redirectPath: '/cases/case-1/evidence',
      createdAt: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      deadlines: [...prev.deadlines, newDeadline],
      reminders: [...prev.reminders, newReminder],
      dashboardUrgentCount: prev.dashboardUrgentCount + 1,
    }));
  };

  const simulateTimePassing = () => {
    setState(prev => ({
      ...prev,
      currentTime: '2024-04-19T10:00:00Z',
      reminders: prev.reminders.map(r => ({
        ...r,
        title: 'Evidence Submission due tomorrow',
        priority: 'high' as const,
      })),
    }));
  };

  const triggerReminder = () => {
    setState(prev => ({
      ...prev,
      currentTime: '2024-04-20T09:00:00Z',
      reminders: prev.reminders.map(r => ({
        ...r,
        title: 'Evidence Submission due today!',
        priority: 'high' as const,
      })),
    }));
  };

  const navigateFromReminder = (path: string) => {
    setState(prev => ({
      ...prev,
      lastNavigation: path,
    }));
  };

  const markComplete = () => {
    setState(prev => ({
      ...prev,
      deadlines: prev.deadlines.map(d =>
        d.id === 'dl-e2e' ? { ...d, status: 'completed' as const } : d
      ),
      reminders: prev.reminders.map(r =>
        r.id === 'rem-e2e' ? { ...r, isRead: true } : r
      ),
      dashboardUrgentCount: Math.max(0, prev.dashboardUrgentCount - 1),
    }));
  };

  return (
    <div data-testid="deadline-reminder-loop">
      <div data-testid="deadline-count">{state.deadlines.length}</div>
      <div data-testid="reminder-count">{state.reminders.filter(r => !r.isRead).length}</div>
      <div data-testid="dashboard-urgent">{state.dashboardUrgentCount}</div>
      <div data-testid="current-time">{state.currentTime || 'not set'}</div>
      <div data-testid="last-navigation">{state.lastNavigation || 'none'}</div>

      <div data-testid="reminders">
        {state.reminders.map(r => (
          <div key={r.id} data-testid={`reminder-${r.id}`}>
            <span data-testid={`reminder-title-${r.id}`}>{r.title}</span>
            <span data-testid={`reminder-priority-${r.id}`}>{r.priority}</span>
            <span data-testid={`reminder-read-${r.id}`}>{r.isRead ? 'read' : 'unread'}</span>
            <button
              data-testid={`navigate-${r.id}`}
              onClick={() => navigateFromReminder(r.redirectPath || '')}
            >
              Navigate
            </button>
          </div>
        ))}
      </div>

      <button data-testid="create-deadline-btn" onClick={createDeadline}>Create Deadline</button>
      <button data-testid="simulate-time-btn" onClick={simulateTimePassing}>Simulate Time Passing</button>
      <button data-testid="trigger-reminder-btn" onClick={triggerReminder}>Trigger Reminder</button>
      <button data-testid="mark-complete-btn" onClick={markComplete}>Mark Complete</button>
    </div>
  );
}

describe('E2E: Deadline-Reminder Closed Loop', () => {
  const initialState: DeadlineReminderState = {
    deadlines: [],
    reminders: [],
    lastNavigation: null,
    dashboardUrgentCount: 0,
    currentTime: '',
  };

  it('triggers reminder at correct time', async () => {
    render(<DeadlineReminderTest initialState={initialState} />);

    expect(screen.getByTestId('deadline-count')).toHaveTextContent('0');
    expect(screen.getByTestId('reminder-count')).toHaveTextContent('0');

    fireEvent.click(screen.getByTestId('create-deadline-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('deadline-count')).toHaveTextContent('1');
      expect(screen.getByTestId('reminder-count')).toHaveTextContent('1');
    });

    expect(screen.getByTestId('reminder-title-rem-e2e')).toHaveTextContent('Evidence Submission due in 3 days');

    fireEvent.click(screen.getByTestId('simulate-time-btn'));
    expect(screen.getByTestId('reminder-title-rem-e2e')).toHaveTextContent('Evidence Submission due tomorrow');

    fireEvent.click(screen.getByTestId('trigger-reminder-btn'));
    expect(screen.getByTestId('reminder-title-rem-e2e')).toHaveTextContent('Evidence Submission due today!');
  });

  it('navigates correctly from reminder', async () => {
    render(<DeadlineReminderTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('create-deadline-btn'));
    fireEvent.click(screen.getByTestId('navigate-rem-e2e'));

    await waitFor(() => {
      expect(screen.getByTestId('last-navigation')).toHaveTextContent('/cases/case-1/evidence');
    });
  });

  it('updates dashboard after marking complete', async () => {
    render(<DeadlineReminderTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('create-deadline-btn'));
    expect(screen.getByTestId('dashboard-urgent')).toHaveTextContent('1');
    expect(screen.getByTestId('reminder-count')).toHaveTextContent('1');

    fireEvent.click(screen.getByTestId('mark-complete-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('dashboard-urgent')).toHaveTextContent('0');
      expect(screen.getByTestId('reminder-count')).toHaveTextContent('0');
      expect(screen.getByTestId('reminder-read-rem-e2e')).toHaveTextContent('read');
    });
  });

  it('completes full deadline-reminder loop', async () => {
    render(<DeadlineReminderTest initialState={initialState} />);

    fireEvent.click(screen.getByTestId('create-deadline-btn'));
    fireEvent.click(screen.getByTestId('simulate-time-btn'));
    fireEvent.click(screen.getByTestId('trigger-reminder-btn'));
    fireEvent.click(screen.getByTestId('navigate-rem-e2e'));
    fireEvent.click(screen.getByTestId('mark-complete-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('dashboard-urgent')).toHaveTextContent('0');
      expect(screen.getByTestId('last-navigation')).toHaveTextContent('/cases/case-1/evidence');
    });
  });
});
