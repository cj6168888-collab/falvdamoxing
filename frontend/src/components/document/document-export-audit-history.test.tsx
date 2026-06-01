import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import axiosInstance from '@/api/client';
import { DocumentExportAuditHistory } from './document-export-audit-history';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;

function renderWithQueryClient(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

beforeEach(() => {
  mockGet.mockReset();
});

describe('DocumentExportAuditHistory', () => {
  it('loads and renders export review audit records', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        total: 1,
        audits: [
          {
            id: 11,
            user_id: 'pytest-user',
            export_action: 'download',
            export_format: 'pdf',
            checked_items: [
              'parties',
              'court_jurisdiction',
              'claims_amounts',
              'facts_evidence',
              'law_validity',
              'evidence_catalog',
              'dates_signature',
              'authorization_consequences',
            ],
            checked_item_count: 8,
            confirmed_at: '2026-06-01T06:30:00Z',
          },
        ],
      },
    });

    renderWithQueryClient(<DocumentExportAuditHistory documentId={9} />);

    await waitFor(() => expect(screen.getByText('文书下载')).toBeInTheDocument());
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('当事人身份')).toBeInTheDocument();
    expect(screen.getByText('法院/管辖/案由')).toBeInTheDocument();
    expect(screen.getByText('授权/发送后果')).toBeInTheDocument();
    expect(screen.getByText(/已确认 8 项/)).toBeInTheDocument();
    expect(screen.getByText(/pytest-user/)).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/documents/9/export-review-audits');
  });

  it('renders empty state for documents without audit records', async () => {
    mockGet.mockResolvedValueOnce({ data: { total: 0, audits: [] } });

    renderWithQueryClient(<DocumentExportAuditHistory documentId="doc-1" />);

    await waitFor(() => expect(screen.getByText('暂无导出核验记录。')).toBeInTheDocument());
  });

  it('does not request audit records without a document id', () => {
    renderWithQueryClient(<DocumentExportAuditHistory documentId={null} />);

    expect(mockGet).not.toHaveBeenCalled();
  });
});
