import { render, screen } from '@testing-library/react';
import { PartyRoleBadge } from './party-role-badge';

describe('PartyRoleBadge', () => {
  it('renders plaintiff variant', () => {
    render(<PartyRoleBadge label="原告" role="plaintiff" />);
    expect(screen.getByText('原告')).toBeInTheDocument();
  });

  it('renders defendant variant', () => {
    render(<PartyRoleBadge label="被告" role="defendant" />);
    expect(screen.getByText('被告')).toBeInTheDocument();
  });

  it('renders third_party variant', () => {
    render(<PartyRoleBadge label="第三人" role="third_party" />);
    expect(screen.getByText('第三人')).toBeInTheDocument();
  });

  it('renders counter_claimant variant', () => {
    render(<PartyRoleBadge label="反诉原告" role="counter_claimant" />);
    expect(screen.getByText('反诉原告')).toBeInTheDocument();
  });

  it('renders counter_defendant variant', () => {
    render(<PartyRoleBadge label="反诉被告" role="counter_defendant" />);
    expect(screen.getByText('反诉被告')).toBeInTheDocument();
  });

  it('defaults to plaintiff when no role provided', () => {
    render(<PartyRoleBadge label="默认" />);
    expect(screen.getByText('默认')).toBeInTheDocument();
  });
});
