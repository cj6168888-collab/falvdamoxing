import { TodaySuggestions } from '@/components/dashboard/today-suggestions';
import { render, screen } from '@/test/test-utils';
import type { TodaySuggestion } from '@/types/dashboard.types';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button' },
}));

const mockSuggestions: TodaySuggestion[] = [
  {
    id: 'sug-1',
    caseId: 'case-1',
    caseTitle: 'Loan Dispute',
    suggestion: '建议补充银行流水作为关键证据',
    priority: 'high',
    title: 'Loan Dispute',
    description: '建议补充银行流水作为关键证据',
    type: 'evidence',
  },
  {
    id: 'sug-2',
    caseId: 'case-2',
    caseTitle: 'Contract Case',
    suggestion: '考虑申请财产保全',
    priority: 'medium',
    title: 'Contract Case',
    description: '考虑申请财产保全',
    type: 'preservation',
  },
  {
    id: 'sug-3',
    caseId: 'case-3',
    caseTitle: 'Property Case',
    suggestion: '整理证人证言清单',
    priority: 'low',
    title: 'Property Case',
    description: '整理证人证言清单',
    type: 'evidence',
  },
];

beforeEach(() => {
  mockNavigate.mockClear();
});

describe('TodaySuggestions', () => {
  it('renders AI suggestions correctly', () => {
    render(
      <TodaySuggestions
        suggestions={mockSuggestions}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('今日建议')).toBeInTheDocument();
    expect(screen.getByText('AI 生成')).toBeInTheDocument();
    expect(screen.getByText('建议补充银行流水作为关键证据')).toBeInTheDocument();
    expect(screen.getByText('考虑申请财产保全')).toBeInTheDocument();
    expect(screen.getByText('整理证人证言清单')).toBeInTheDocument();
  });

  it('shows empty state when no suggestions', () => {
    render(
      <TodaySuggestions
        suggestions={[]}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('暂无建议')).toBeInTheDocument();
    expect(
      screen.getByText('AI 正在分析您的案件，稍后将生成个性化建议'),
    ).toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading is true', () => {
    render(
      <TodaySuggestions
        suggestions={[]}
        isLoading={true}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('今日建议')).toBeInTheDocument();
    expect(screen.getByText('AI 生成')).toBeInTheDocument();
  });

  it('navigates to case page when suggestion is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TodaySuggestions
        suggestions={mockSuggestions}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    const suggestionButtons = screen.getAllByRole('button');
    await user.click(suggestionButtons[0]);

    expect(mockNavigate).toHaveBeenCalledWith('/cases/case-1');
  });

  it('shows priority labels for each suggestion', () => {
    render(
      <TodaySuggestions
        suggestions={mockSuggestions}
        isLoading={false}
        isError={false}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText('高优先')).toBeInTheDocument();
    expect(screen.getByText('中优先')).toBeInTheDocument();
    expect(screen.getByText('低优先')).toBeInTheDocument();
  });
});
