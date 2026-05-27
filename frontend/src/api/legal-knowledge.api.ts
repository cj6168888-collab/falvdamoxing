import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { LawItem, InterpretationItem, GuidingCaseItem, LegalStats, SearchResult } from '@/types/legal-knowledge.types';

// ============ Queries ============

export function useLaws(keyword?: string, category?: string, lawName?: string, page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: ['legal-laws', keyword, category, lawName, page, pageSize],
    queryFn: () => axiosInstance.get<{ laws: LawItem[]; total: number; page: number; page_size: number }>(
      '/api/legal-knowledge/laws',
      { params: { keyword, category, law_name: lawName, page, page_size: pageSize } }
    ).then(res => res.data),
    enabled: !!keyword,
  });
}

export function useLawDetail(lawId: string) {
  return useQuery({
    queryKey: ['legal-law-detail', lawId],
    queryFn: () => axiosInstance.get(`/api/legal-knowledge/laws/${lawId}`).then(res => res.data),
    enabled: !!lawId,
  });
}

export function useInterpretations(keyword?: string, page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: ['legal-interpretations', keyword, page, pageSize],
    queryFn: () => axiosInstance.get<{ interpretations: InterpretationItem[]; total: number; page: number; page_size: number }>(
      '/api/legal-knowledge/interpretations',
      { params: { keyword, page, page_size: pageSize } }
    ).then(res => res.data),
    enabled: !!keyword,
  });
}

export function useCases(keyword?: string, caseType?: string, page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: ['legal-cases', keyword, caseType, page, pageSize],
    queryFn: () => axiosInstance.get<{ cases: GuidingCaseItem[]; total: number; page: number; page_size: number }>(
      '/api/legal-knowledge/cases',
      { params: { keyword, case_type: caseType, page, page_size: pageSize } }
    ).then(res => res.data),
    enabled: !!keyword,
  });
}

export function useCaseDetail(caseId: string) {
  return useQuery({
    queryKey: ['legal-case-detail', caseId],
    queryFn: () => axiosInstance.get(`/api/legal-knowledge/cases/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

export function useStats() {
  return useQuery({
    queryKey: ['legal-stats'],
    queryFn: () => axiosInstance.get<LegalStats>('/api/legal-knowledge/stats').then(res => res.data),
  });
}

export function useSemanticSearch(keyword?: string, searchType?: string, limit: number = 20) {
  return useQuery({
    queryKey: ['legal-semantic-search', keyword, searchType],
    queryFn: () => axiosInstance.get<SearchResult>(
      '/api/legal-knowledge/search',
      { params: { keyword, search_type: searchType, limit } }
    ).then(res => res.data),
    enabled: !!keyword && keyword.length >= 2,
  });
}

// ============ Mutations ============

export function useTriggerImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => axiosInstance.post('/api/legal-knowledge/import').then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-stats'] });
    },
  });
}

export function useExportData(exportType: string = 'all', format: string = 'json') {
  return useMutation({
    mutationFn: () => axiosInstance.get('/api/legal-knowledge/export', { params: { export_type: exportType, format } }).then(res => res.data),
  });
}
