import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useChatHistory(caseId: string) {
  return useQuery({
    queryKey: ['chat-history', caseId],
    queryFn: () => axiosInstance.get(`/api/v2/assistant/conversation-history/${caseId}`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function sendChatMessage(caseId: string, message: string) {
  return axiosInstance.post('/api/v2/assistant/chat', { case_id: parseInt(caseId), message }, {
    timeout: 120000,
  });
}

export async function getQuickActions(caseId: string) {
  return axiosInstance.get(`/api/v2/assistant/quick-actions/${caseId}`).then(res => res.data);
}
