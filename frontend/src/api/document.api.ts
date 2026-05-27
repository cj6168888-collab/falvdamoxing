import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Document as CaseDocument, DocumentTemplate } from '@/types/document.types';

interface BackendDocument {
  id: number | string;
  title?: string;
  document_type?: string;
  type?: string;
  content?: string;
  version?: number;
  status?: CaseDocument['status'];
  referenced_evidence?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
}

export function useDocuments(caseId: string) {
  return useQuery({
    queryKey: ['documents', caseId],
    queryFn: () => axiosInstance.get<BackendDocument[]>(`/api/document-management/case/${caseId}/generated`).then(res =>
      (res.data || []).map<CaseDocument>((d) => ({
        id: String(d.id),
        caseId: String(caseId),
        title: d.title || '',
        type: d.document_type || d.type || '',
        content: d.content || '',
        version: d.version || 1,
        status: d.status || 'draft',
        relatedEvidence: d.referenced_evidence ? [d.referenced_evidence] : [],
        relatedIssues: [],
        createdAt: d.created_at || d.createdAt || '',
        updatedAt: d.updated_at || d.updatedAt || '',
      }))
    ),
    enabled: !!caseId,
  });
}

export function useTemplates() {
  return useQuery({
    queryKey: ['document-templates'],
    queryFn: () => axiosInstance.get<DocumentTemplate[]>('/api/documents/templates/list').then(res => res.data),
  });
}

export async function generateDocument(caseId: string, data: Record<string, unknown> & { type?: string; template?: string; prompt?: string }) {
  return axiosInstance.post(`/api/documents/generate/enhanced`, { caseId, ...data }).then(res => res.data);
}

export async function getDocumentSuggestions(caseId: string) {
  return axiosInstance.get(`/api/document-management/case/${caseId}/suggestions`).then(res => res.data);
}
