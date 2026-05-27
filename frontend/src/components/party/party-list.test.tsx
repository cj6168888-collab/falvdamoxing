import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { PartyList } from './party-list';
import { mockParties } from '@/test/fixtures';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

describe('PartyList', () => {
  it('renders party list with all parties', () => {
    render(
      <PartyList
        parties={mockParties}
        isLoading={false}
        onAdd={vi.fn()}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Zhang San')).toBeInTheDocument();
    expect(screen.getByText('Li Si')).toBeInTheDocument();
    expect(screen.getByText('Wang Wu')).toBeInTheDocument();
    expect(screen.getByText('Zhao Liu')).toBeInTheDocument();
  });

  it('shows party roles', () => {
    render(
      <PartyList
        parties={mockParties}
        isLoading={false}
        onAdd={vi.fn()}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText(/plaintiff/)).toBeInTheDocument();
    expect(screen.getByText(/defendant/)).toBeInTheDocument();
    expect(screen.getByText(/third_party/)).toBeInTheDocument();
  });

  it('shows empty state when no parties', () => {
    render(
      <PartyList
        parties={[]}
        isLoading={false}
        onAdd={vi.fn()}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('暂无当事人')).toBeInTheDocument();
    expect(screen.getByText('添加当事人')).toBeInTheDocument();
  });

  it('calls onAdd when add button is clicked', () => {
    const onAdd = vi.fn();
    render(
      <PartyList
        parties={[]}
        isLoading={false}
        onAdd={onAdd}
        onSelect={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText('添加当事人'));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(
      <PartyList
        parties={[]}
        isLoading={true}
        onAdd={vi.fn()}
        onSelect={vi.fn()}
      />
    );

    expect(screen.queryByText('暂无当事人')).not.toBeInTheDocument();
    expect(screen.queryByText('Zhang San')).not.toBeInTheDocument();
  });
});
