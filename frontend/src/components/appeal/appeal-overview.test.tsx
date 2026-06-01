import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { AppealOverview } from './appeal-overview';
import { generateAppealPetition } from '@/api/appeal.api';

vi.mock('@/api/appeal.api', () => ({
  useAppeals: () => ({
    data: {
      appeals: [
        {
          id: 7,
          appeal_type: 'first_to_second',
          appeal_status: 'preparing',
          appellant_type: '原告',
          appellant_name: '陈靖',
          appeal_reason: '事实认定错误',
        },
      ],
      total: 1,
    },
    isLoading: false,
  }),
  useCreateAppeal: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useAppealStatistics: () => ({
    data: {
      total_appeals: 1,
      total_arguments: 0,
      key_arguments: 0,
      prepared_documents: 0,
      total_documents: 0,
    },
  }),
  useAppealArguments: () => ({ data: { arguments: [], total: 0 }, isLoading: false }),
  useCreateAppealArgument: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteAppealArgument: () => ({ mutate: vi.fn() }),
  useAppealDeadlines: () => ({ data: { deadlines: [], total: 0 }, isLoading: false }),
  useCreateAppealDeadline: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useAppealDocuments: () => ({ data: { documents: [], total: 0 }, isLoading: false }),
  useCreateAppealDocument: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useAppealStrategy: () => ({ data: { strategy: null }, isLoading: false }),
  generateAppealPetition: vi.fn(() => Promise.resolve({ requires_human_review: true })),
}));

vi.mock('./appeal-arguments-panel', () => ({
  AppealArgumentsPanel: () => <div>上诉论点面板</div>,
}));

vi.mock('./appeal-deadline-panel', () => ({
  AppealDeadlinePanel: () => <div>期限追踪面板</div>,
}));

vi.mock('./appeal-documents-panel', () => ({
  AppealDocumentsPanel: () => <div>上诉材料面板</div>,
}));

vi.mock('./appeal-strategy-panel', () => ({
  AppealStrategyPanel: () => <div>二审策略面板</div>,
}));

describe('AppealOverview', () => {
  it('frames appeal petition output as a draft to be reviewed', async () => {
    const user = userEvent.setup();
    render(<AppealOverview caseId="42" />);

    await user.click(screen.getByText('陈靖'));
    await user.click(screen.getByRole('tab', { name: '上诉详情' }));

    expect(await screen.findByRole('button', { name: /起草上诉状草稿/ })).toBeInTheDocument();
    expect(screen.queryByText(/AI\s*生成上诉状/)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /起草上诉状草稿/ }));
    expect(generateAppealPetition).toHaveBeenCalledWith('7');
  });
});
