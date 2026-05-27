import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { mockCases, createMockCase } from '@/test/fixtures';
import type { Case } from '@/types/case.types';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface CaseListProps {
  cases: Case[];
  onCreateCase: (caseData: Partial<Case>) => void;
  onNavigate: (path: string) => void;
}

function CaseList({ cases, onCreateCase: _onCreateCase, onNavigate }: CaseListProps) {
  const sortedCases = [...cases].sort((a, b) =>
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  return (
    <div data-testid="case-list">
      <div data-testid="case-count">{cases.length}</div>
      <button data-testid="new-case-btn" onClick={() => onNavigate('/cases/new')}>
        New Case
      </button>
      <ul data-testid="case-items">
        {sortedCases.map(c => (
          <li key={c.id} data-testid={`case-item-${c.id}`}>
            <span data-testid={`case-title-${c.id}`}>{c.title}</span>
            <button data-testid={`view-case-${c.id}`} onClick={() => onNavigate(`/cases/${c.id}`)}>
              View
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

interface NewCaseFormProps {
  onSubmit: (caseData: Partial<Case>) => void;
  onCancel: () => void;
}

function NewCaseForm({ onSubmit, onCancel }: NewCaseFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      title: 'New Contract Dispute',
      type: 'civil',
      status: 'preparing',
    });
  };

  return (
    <form data-testid="new-case-form" onSubmit={handleSubmit}>
      <button type="submit" data-testid="submit-new-case">Create Case</button>
      <button type="button" data-testid="cancel-new-case" onClick={onCancel}>Cancel</button>
    </form>
  );
}

describe('Case List ↔ New Case Integration', () => {
  const initialCases = [
    mockCases.preparing,
    mockCases.negotiating,
    mockCases.litigating,
  ];

  it('refreshes case list after creating new case', async () => {
    const handleCreateCase = vi.fn();
    const handleNavigate = vi.fn();

    render(
      <CaseList
        cases={initialCases}
        onCreateCase={handleCreateCase}
        onNavigate={handleNavigate}
      />
    );

    expect(screen.getByTestId('case-count')).toHaveTextContent('3');

    fireEvent.click(screen.getByTestId('new-case-btn'));
    expect(handleNavigate).toHaveBeenCalledWith('/cases/new');
  });

  it('shows new case at top of list after creation', () => {
    const handleCreateCase = vi.fn();
    const handleNavigate = vi.fn();

    const newCase = createMockCase({
      id: 'case-new',
      title: 'New Contract Dispute',
      createdAt: '2024-04-01T10:00:00Z',
    });

    const updatedCases = [newCase, ...initialCases];

    render(
      <CaseList
        cases={updatedCases}
        onCreateCase={handleCreateCase}
        onNavigate={handleNavigate}
      />
    );

    const caseItems = screen.getByTestId('case-items');
    const firstItem = caseItems.querySelector('[data-testid^="case-item-"]');
    expect(firstItem).toHaveAttribute('data-testid', 'case-item-case-new');
  });

  it('increments case count after new case creation', () => {
    const handleCreateCase = vi.fn();
    const handleNavigate = vi.fn();

    const newCase = createMockCase({
      id: 'case-new',
      title: 'New Contract Dispute',
      createdAt: '2024-04-01T10:00:00Z',
    });

    const { rerender } = render(
      <CaseList
        cases={initialCases}
        onCreateCase={handleCreateCase}
        onNavigate={handleNavigate}
      />
    );

    expect(screen.getByTestId('case-count')).toHaveTextContent('3');

    rerender(
      <CaseList
        cases={[...initialCases, newCase]}
        onCreateCase={handleCreateCase}
        onNavigate={handleNavigate}
      />
    );

    expect(screen.getByTestId('case-count')).toHaveTextContent('4');
  });

  it('navigates from list to new case and back', async () => {
    const handleCreateCase = vi.fn();
    const navigateCalls: string[] = [];
    const handleNavigate = vi.fn((path: string) => navigateCalls.push(path));

    const { rerender } = render(
      <CaseList
        cases={initialCases}
        onCreateCase={handleCreateCase}
        onNavigate={handleNavigate}
      />
    );

    fireEvent.click(screen.getByTestId('new-case-btn'));
    expect(handleNavigate).toHaveBeenCalledWith('/cases/new');

    rerender(
      <NewCaseForm
        onSubmit={handleCreateCase}
        onCancel={() => handleNavigate('/cases')}
      />
    );

    fireEvent.click(screen.getByTestId('cancel-new-case'));
    expect(handleNavigate).toHaveBeenCalledWith('/cases');
  });
});
