import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import { createParty, deleteParty, updateParty, useParties } from './party.api';
import type { Party } from '@/types/party.types';
import type { ReactNode } from 'react';
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

const party: Party = {
  id: 'party-1',
  caseId: 'case-1',
  name: 'Plaintiff',
  role: 'plaintiff',
  createdAt: '2026-05-01T00:00:00.000Z',
  updatedAt: '2026-05-01T00:00:00.000Z',
};

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('party api hooks', () => {
  it('loads parties by case id', async () => {
    mockGet.mockResolvedValueOnce({ data: [party] });

    const { result } = renderHook(() => useParties('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual([party]));
    expect(mockGet).toHaveBeenCalledWith('/api/cases/case-1/parties');
  });

  it('does not request parties without a case id', () => {
    renderHook(() => useParties(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('party api commands', () => {
  it('creates a party', async () => {
    mockPost.mockResolvedValueOnce({ data: party });

    await expect(createParty('case-1', { name: 'Plaintiff' })).resolves.toEqual(party);
    expect(mockPost).toHaveBeenCalledWith('/api/cases/case-1/parties', { name: 'Plaintiff' });
  });

  it('updates a party', async () => {
    mockPut.mockResolvedValueOnce({ data: { ...party, phone: '123' } });

    await expect(updateParty('case-1', 'party-1', { phone: '123' })).resolves.toEqual({
      ...party,
      phone: '123',
    });
    expect(mockPut).toHaveBeenCalledWith('/api/cases/case-1/parties/party-1', { phone: '123' });
  });

  it('deletes a party', async () => {
    const response = { status: 204 };
    mockDelete.mockResolvedValueOnce(response);

    await expect(deleteParty('case-1', 'party-1')).resolves.toEqual(response);
    expect(mockDelete).toHaveBeenCalledWith('/api/cases/case-1/parties/party-1');
  });
});
