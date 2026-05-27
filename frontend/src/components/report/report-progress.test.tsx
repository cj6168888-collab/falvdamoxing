import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ReportProgress } from './report-progress';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('ReportProgress', () => {
  it('renders progress bar', () => {
    render(<ReportProgress progress={50} />);

    expect(screen.getByText('生成进度')).toBeInTheDocument();
  });

  it('shows progress percentage', () => {
    render(<ReportProgress progress={75} />);

    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('shows current step', () => {
    render(<ReportProgress progress={50} currentSection="Analyzing evidence" />);

    expect(screen.getByText(/Analyzing evidence/)).toBeInTheDocument();
  });

  it('shows completed state at 100%', () => {
    render(<ReportProgress progress={100} currentSection="Completed" />);

    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText(/Completed/)).toBeInTheDocument();
  });

  it('renders with zero progress', () => {
    render(<ReportProgress progress={0} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
  });
});
