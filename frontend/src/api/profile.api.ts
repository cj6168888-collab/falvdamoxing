import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { ProfileSummary, KnowledgeGraphData, EvidenceGap } from '@/types/profile.types';

export function useProfile(caseId: string) {
  return useQuery<ProfileSummary>({
    queryKey: ['profile', caseId],
    queryFn: () => axiosInstance.get(`/api/v2/profile/summary/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function getKnowledgeGraph(caseId: string) {
  return axiosInstance.get<KnowledgeGraphData>(`/api/v2/profile/knowledge-graph/${caseId}`).then(res => res.data);
}

export function useKnowledgeGraph(caseId: string) {
  return useQuery<KnowledgeGraphData>({
    queryKey: ['knowledge-graph', caseId],
    queryFn: () => getKnowledgeGraph(caseId),
    enabled: !!caseId,
  });
}

export function useEvidenceGaps(caseId: string) {
  return useQuery<EvidenceGap>({
    queryKey: ['evidence-gaps', caseId],
    queryFn: () => axiosInstance.get(`/api/v2/profile/gaps/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function recordInteraction(caseId: number, userInput: string, inputType: string, systemResponse = '') {
  return axiosInstance.post('/api/v2/profile/interaction', {
    case_id: caseId,
    user_input: userInput,
    input_type: inputType,
    system_response: systemResponse,
  }).then(res => res.data);
}

export async function queryKnowledge(caseId: number, query: string, knowledgeType?: string) {
  return axiosInstance.post('/api/v2/profile/knowledge/query', {
    case_id: caseId,
    query,
    knowledge_type: knowledgeType,
  }).then(res => res.data);
}

export async function resolveGap(caseId: number, gapId: string, resolution: string) {
  return axiosInstance.post('/api/v2/profile/gap/resolve', {
    case_id: caseId,
    gap_id: gapId,
    resolution,
  }).then(res => res.data);
}

export async function buildProfile(caseId: number, useAi = true) {
  return axiosInstance.post('/api/v2/profile/build', {
    case_id: caseId,
    use_ai: useAi,
  }).then(res => res.data);
}

export function useBuildProfile(caseId: string) {
  const queryClient = useQueryClient();
  const { mutate, isPending, data } = useMutation({
    mutationFn: () => buildProfile(Number(caseId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', caseId] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-graph', caseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-gaps', caseId] });
    },
  });
  return { build: mutate, isBuilding: isPending, result: data };
}
