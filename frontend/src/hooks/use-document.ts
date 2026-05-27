import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { generateDocument, getDocumentSuggestions } from '@/api/document.api';
import { useDocuments, useTemplates } from '@/api/document.api';

export function useDocumentList(caseId: string) {
  return useDocuments(caseId);
}

export function useDocumentTemplates() {
  return useTemplates();
}

export function useGenerateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, data }: { caseId: string; data: Record<string, unknown> & { type?: string; template?: string; prompt?: string } }) =>
      generateDocument(caseId, data),
    onSuccess: (_, { caseId }) => {
      queryClient.invalidateQueries({ queryKey: ['documents', caseId] });
    },
  });
}

export function useDocumentSuggestions(caseId: string) {
  return useQuery({
    queryKey: ['document-suggestions', caseId],
    queryFn: () => getDocumentSuggestions(caseId),
    enabled: !!caseId,
  });
}
