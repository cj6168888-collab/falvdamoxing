import { render, screen } from '@/test/test-utils';
import { UrgencyBadge } from './urgency-badge';

describe('UrgencyBadge', () => {
  it('renders expired status correctly', () => {
    render(<UrgencyBadge daysRemaining={-5} urgency="expired" />);

    const badge = screen.getByText('已过期 5 天');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-red-100');
    expect(badge.className).toContain('text-red-700');
  });

  it('renders today expiry', () => {
    render(<UrgencyBadge daysRemaining={0} urgency="urgent" />);

    const badge = screen.getByText('今天到期');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-amber-100');
    expect(badge.className).toContain('text-amber-700');
  });

  it('renders remaining days', () => {
    render(<UrgencyBadge daysRemaining={7} urgency="warning" />);

    const badge = screen.getByText('还剩 7 天');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-yellow-100');
    expect(badge.className).toContain('text-yellow-700');
  });

  it('renders normal urgency', () => {
    render(<UrgencyBadge daysRemaining={30} urgency="normal" />);

    const badge = screen.getByText('还剩 30 天');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-green-100');
    expect(badge.className).toContain('text-green-700');
  });
});
