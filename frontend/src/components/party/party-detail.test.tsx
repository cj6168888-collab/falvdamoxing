import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { PartyDetail } from './party-detail';
import { createMockParty } from '@/test/fixtures';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

vi.mock('@/components/common/company-info', () => ({
  CompanyInfo: ({ name }: { name: string }) => <div>{name}</div>,
}));

describe('PartyDetail', () => {
  it('renders party information', () => {
    const party = createMockParty();
    render(
      <PartyDetail
        party={party}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('Zhang San')).toBeInTheDocument();
    expect(screen.getByText('13800138000')).toBeInTheDocument();
    expect(screen.getByText('zhangsan@example.com')).toBeInTheDocument();
    expect(screen.getByText('Beijing Chaoyang District')).toBeInTheDocument();
  });

  it('shows role', () => {
    const party = createMockParty();
    render(
      <PartyDetail
        party={party}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('plaintiff')).toBeInTheDocument();
  });

  it('shows edit button', () => {
    const party = createMockParty();
    render(
      <PartyDetail
        party={party}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText('编辑')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = vi.fn();
    const party = createMockParty();
    render(
      <PartyDetail
        party={party}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('编辑'));
    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it('hides optional fields when not provided', () => {
    const party = createMockParty({ phone: undefined, email: undefined, address: undefined });
    render(
      <PartyDetail
        party={party}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.queryByText('13800138000')).not.toBeInTheDocument();
    expect(screen.queryByText('zhangsan@example.com')).not.toBeInTheDocument();
    expect(screen.queryByText('Beijing Chaoyang District')).not.toBeInTheDocument();
  });
});
