import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { UrgencyReport } from '@/components/timeline/urgency-report';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button' },
}));

const mockDeadlines = [
  { title: '举证期限', dueDate: '2024-04-10', daysRemaining: 3 },
  { title: '答辩期限', dueDate: '2024-04-05', daysRemaining: -2 },
  { title: '上诉期限', dueDate: '2024-04-20', daysRemaining: 7 },
  { title: '执行申请', dueDate: '2024-06-01', daysRemaining: 60 },
];

describe('UrgencyReport', () => {
  it('renders urgency summary with urgent items only', () => {
    render(<UrgencyReport deadlines={mockDeadlines} />);

    expect(screen.getByText('紧迫度报告')).toBeInTheDocument();
    expect(screen.getByText('举证期限')).toBeInTheDocument();
    expect(screen.getByText('答辩期限')).toBeInTheDocument();
    expect(screen.getByText('上诉期限')).toBeInTheDocument();
    expect(screen.queryByText('执行申请')).not.toBeInTheDocument();
  });

  it('shows count by urgency level', () => {
    render(<UrgencyReport deadlines={mockDeadlines} />);

    expect(screen.getByText('3 天')).toBeInTheDocument();
    expect(screen.getByText('-2 天')).toBeInTheDocument();
    expect(screen.getByText('7 天')).toBeInTheDocument();
  });

  it('sorts urgent items by days remaining ascending', () => {
    render(<UrgencyReport deadlines={mockDeadlines} />);

    const daysElements = screen.getAllByText(/\d+ 天/);
    const daysValues = daysElements.map((el) => parseInt(el.textContent || '0'));

    for (let i = 1; i < daysValues.length; i++) {
      expect(daysValues[i]).toBeGreaterThanOrEqual(daysValues[i - 1]);
    }
  });

  it('shows empty state when no urgent deadlines', () => {
    const nonUrgentDeadlines = [
      { title: '执行申请', dueDate: '2024-06-01', daysRemaining: 60 },
      { title: '普通期限', dueDate: '2024-08-01', daysRemaining: 120 },
    ];

    render(<UrgencyReport deadlines={nonUrgentDeadlines} />);

    expect(screen.getByText('紧迫度报告')).toBeInTheDocument();
    expect(screen.queryByText('执行申请')).not.toBeInTheDocument();
  });

  it('formats dates correctly', () => {
    render(<UrgencyReport deadlines={mockDeadlines} />);

    const dateElements = screen.getAllByText(/年.*月.*日/);
    expect(dateElements.length).toBeGreaterThan(0);
  });
});
