import { fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ExecutionDashboard } from './execution-dashboard';
import { generateExecutionApplication } from '@/api/execution.api';

vi.mock('@/api/execution.api', () => ({
  useExecutionOverview: () => ({
    data: {
      status: 'pending',
      progress: 0,
      total_tasks: 0,
      total_assets: 0,
    },
    isLoading: false,
  }),
  useExecutionRecords: () => ({ data: { records: [], total: 0 } }),
  useExecutionTasks: () => ({ data: { tasks: [], total: 0 } }),
  useExecutionAssets: () => ({ data: { assets: [], total: 0 } }),
  useCreateExecutionRecord: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreateExecutionTask: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreateExecutionAsset: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteExecutionTask: () => ({ mutate: vi.fn() }),
  useUpdateExecutionTask: () => ({ mutateAsync: vi.fn() }),
  generateExecutionApplication: vi.fn(() => Promise.resolve({ requires_human_review: true })),
}));

describe('ExecutionDashboard', () => {
  it('frames execution application output as a draft to be reviewed', () => {
    render(<ExecutionDashboard caseId="42" />);

    expect(screen.getByRole('button', { name: /起草执行申请书草稿/ })).toBeInTheDocument();
    expect(screen.queryByText(/AI\s*生成执行申请书/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /起草执行申请书草稿/ }));
    expect(generateExecutionApplication).toHaveBeenCalledWith('42');
  });
});
