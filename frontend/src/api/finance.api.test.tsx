import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  useAssessWinRate,
  useCostAnalysis,
  useCreateExpense,
  useDeleteExpense,
  useExpenses,
  useFinanceOverview,
  useFinanceStatistics,
  useUpdateExpense,
  useUpdateFinanceOverview,
  useWinRate,
} from './finance.api';
import type { ReactNode } from 'react';
import type { ExpenseRecord } from '@/types/finance.types';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;
const mockPut = axiosInstance.put as Mock;
const mockDelete = axiosInstance.delete as Mock;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('finance api queries', () => {
  it('loads finance resources', async () => {
    const responses: Record<string, unknown> = {
      '/api/finance/case/case-1': { expected_recovery: 1000 },
      '/api/finance/case/case-1/expenses': { expenses: [{ id: 1 }], total: 1 },
      '/api/finance/case/case-1/cost-analysis': { roi: 2 },
      '/api/finance/case/case-1/win-rate': { win_rate: 0.7 },
      '/api/finance/case/case-1/statistics': { total_expenses: 100 },
    };
    mockGet.mockImplementation((url: string) => Promise.resolve({ data: responses[url] }));

    const overviewHook = renderHook(() => useFinanceOverview('case-1'), { wrapper: createWrapper() });
    const expensesHook = renderHook(() => useExpenses('case-1'), { wrapper: createWrapper() });
    const costHook = renderHook(() => useCostAnalysis('case-1'), { wrapper: createWrapper() });
    const winRateHook = renderHook(() => useWinRate('case-1'), { wrapper: createWrapper() });
    const statsHook = renderHook(() => useFinanceStatistics('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(overviewHook.result.current.data).toEqual({ expected_recovery: 1000 }));
    await waitFor(() => expect(expensesHook.result.current.data).toEqual({ expenses: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(costHook.result.current.data).toEqual({ roi: 2 }));
    await waitFor(() => expect(winRateHook.result.current.data).toEqual({ win_rate: 0.7 }));
    await waitFor(() => expect(statsHook.result.current.data).toEqual({ total_expenses: 100 }));

    Object.keys(responses).forEach((url) => {
      expect(mockGet).toHaveBeenCalledWith(url);
    });
  });

  it('does not request finance resources without a case id', () => {
    renderHook(() => useFinanceOverview(''), { wrapper: createWrapper() });
    renderHook(() => useExpenses(''), { wrapper: createWrapper() });
    renderHook(() => useCostAnalysis(''), { wrapper: createWrapper() });
    renderHook(() => useWinRate(''), { wrapper: createWrapper() });
    renderHook(() => useFinanceStatistics(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('finance api mutations', () => {
  it('updates overview and manages expenses', async () => {
    mockPut.mockResolvedValue({ data: { updated: true } });
    mockPost.mockResolvedValue({ data: { created: true } });
    mockDelete.mockResolvedValue({ data: { deleted: true } });

    const updateOverview = renderHook(() => useUpdateFinanceOverview('case-1'), { wrapper: createWrapper() });
    const createExpense = renderHook(() => useCreateExpense('case-1'), { wrapper: createWrapper() });
    const updateExpense = renderHook(() => useUpdateExpense(), { wrapper: createWrapper() });
    const deleteExpense = renderHook(() => useDeleteExpense('case-1'), { wrapper: createWrapper() });
    const assessWinRate = renderHook(() => useAssessWinRate('case-1'), { wrapper: createWrapper() });

    await updateOverview.result.current.mutateAsync({ expected_recovery: 2000 });
    const newExpense: Partial<ExpenseRecord> = { amount: 100 };
    const expenseUpdate: Partial<ExpenseRecord> = { amount: 120 };

    await createExpense.result.current.mutateAsync(newExpense);
    await updateExpense.result.current.mutateAsync({ expenseId: 1, data: expenseUpdate });
    await deleteExpense.result.current.mutateAsync(1);
    await assessWinRate.result.current.mutateAsync(true);

    expect(mockPut).toHaveBeenNthCalledWith(1, '/api/finance/case/case-1', { expected_recovery: 2000 });
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/finance/case/case-1/expenses', newExpense);
    expect(mockPut).toHaveBeenNthCalledWith(2, '/api/finance/expenses/1', expenseUpdate);
    expect(mockDelete).toHaveBeenCalledWith('/api/finance/expenses/1');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/finance/case/case-1/win-rate', null, { params: { force: true } });
  });
});
