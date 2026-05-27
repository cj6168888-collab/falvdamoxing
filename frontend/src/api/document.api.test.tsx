import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  generateDocument,
  getDocumentSuggestions,
  useDocuments,
  useTemplates,
} from './document.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;

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
});

describe('document api hooks', () => {
  it('loads and transforms generated documents', async () => {
    mockGet.mockResolvedValueOnce({
      data: [
        {
          id: 9,
          title: 'Complaint',
          document_type: 'complaint',
          content: 'content',
          status: 'review',
          referenced_evidence: 'ev-1',
          created_at: '2026-05-01T00:00:00.000Z',
          updated_at: '2026-05-02T00:00:00.000Z',
          modification_history: [{ note: 'edited' }],
        },
      ],
    });

    const { result } = renderHook(() => useDocuments('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.[0]?.id).toBe('9'));
    expect(result.current.data?.[0]).toMatchObject({
      caseId: 'case-1',
      title: 'Complaint',
      type: 'complaint',
      content: 'content',
      version: 1,
      status: 'review',
      relatedEvidence: ['ev-1'],
      relatedIssues: [],
      createdAt: '2026-05-01T00:00:00.000Z',
      updatedAt: '2026-05-02T00:00:00.000Z',
    });
    expect(mockGet).toHaveBeenCalledWith('/api/document-management/case/case-1/generated');
  });

  it('does not request documents without a case id', () => {
    renderHook(() => useDocuments(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('loads document templates', async () => {
    const templates = [{ id: 'tpl-1', name: 'Complaint', type: 'complaint' }];
    mockGet.mockResolvedValueOnce({ data: templates });

    const { result } = renderHook(() => useTemplates(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(templates));
    expect(mockGet).toHaveBeenCalledWith('/api/documents/templates/list');
  });
});

describe('document api commands', () => {
  it('generates a document', async () => {
    const response = { id: 'doc-new', title: 'Generated' };
    mockPost.mockResolvedValueOnce({ data: response });

    await expect(generateDocument('case-1', { type: 'complaint', prompt: 'draft' })).resolves.toEqual(response);
    expect(mockPost).toHaveBeenCalledWith('/api/documents/generate/enhanced', {
      caseId: 'case-1',
      type: 'complaint',
      prompt: 'draft',
    });
  });

  it('loads document suggestions', async () => {
    const suggestions = [{ type: 'complaint', reason: 'required' }];
    mockGet.mockResolvedValueOnce({ data: suggestions });

    await expect(getDocumentSuggestions('case-1')).resolves.toEqual(suggestions);
    expect(mockGet).toHaveBeenCalledWith('/api/document-management/case/case-1/suggestions');
  });
});
