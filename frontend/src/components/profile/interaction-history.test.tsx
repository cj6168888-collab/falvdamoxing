import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { InteractionHistory } from './interaction-history';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

vi.mock('@/lib/date', () => ({
  formatChineseDate: (date: string) => date,
}));

describe('InteractionHistory', () => {
  it('renders interaction timeline', () => {
    const interactions = [
      { action: 'Submitted evidence', timestamp: '2024-01-15' },
      { action: 'Viewed case details', timestamp: '2024-01-16' },
    ];

    render(<InteractionHistory interactions={interactions} />);

    expect(screen.getByText('Submitted evidence')).toBeInTheDocument();
    expect(screen.getByText('Viewed case details')).toBeInTheDocument();
  });

  it('shows interaction types and dates', () => {
    const interactions = [
      { action: 'Uploaded document', timestamp: '2024-02-20' },
    ];

    render(<InteractionHistory interactions={interactions} />);

    expect(screen.getByText('Uploaded document')).toBeInTheDocument();
    expect(screen.getByText('2024-02-20')).toBeInTheDocument();
  });

  it('shows interaction count', () => {
    const interactions = [
      { action: 'Action 1', timestamp: '2024-01-01' },
      { action: 'Action 2', timestamp: '2024-01-02' },
      { action: 'Action 3', timestamp: '2024-01-03' },
    ];

    render(<InteractionHistory interactions={interactions} />);

    const items = screen.getAllByText(/Action/);
    expect(items.length).toBe(3);
  });

  it('renders empty state when no interactions', () => {
    render(<InteractionHistory interactions={[]} />);

    expect(screen.queryByText(/Action/)).not.toBeInTheDocument();
  });
});
