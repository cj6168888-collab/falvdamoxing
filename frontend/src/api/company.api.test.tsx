import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import { ServerError } from '@/api/client';
import axiosInstance from '@/api/client';
import { CompanyInfoUnavailableError, searchCompany, useCompanyInfo } from './company.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import type * as ClientModule from '@/api/client';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof ClientModule>();

  return {
    ...actual,
    default: {
      get: vi.fn(),
    },
  };
});

const mockGet = axiosInstance.get as Mock;

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
});

describe('company api', () => {
  it('loads company info with an encoded company name', async () => {
    mockGet.mockResolvedValueOnce({ data: { name: 'ACME & Co' } });

    const { result } = renderHook(() => useCompanyInfo('ACME & Co'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual({ name: 'ACME & Co' }));
    expect(mockGet).toHaveBeenCalledWith('/api/company-info/ACME%20%26%20Co');
  });

  it('does not request company info without a company name', () => {
    renderHook(() => useCompanyInfo(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('searches company by keyword', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ name: 'ACME' }] });

    await expect(searchCompany('ACME')).resolves.toEqual([{ name: 'ACME' }]);
    expect(mockGet).toHaveBeenCalledWith('/api/company-info/search', { params: { keyword: 'ACME' } });
  });

  it('maps unconfigured company provider responses to a specific error', async () => {
    mockGet.mockRejectedValueOnce(
      new ServerError(
        'COMPANY_INFO_API_BASE_URL and COMPANY_INFO_API_KEY are not configured',
        503,
      ),
    );

    await expect(searchCompany('ACME')).rejects.toBeInstanceOf(CompanyInfoUnavailableError);
  });
});
