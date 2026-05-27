import { useQuery, useMutation } from '@tanstack/react-query';
import { sendChatMessage, getQuickActions } from '@/api/chat.api';
import { useChatStore } from '@/stores/chat.store';

type MessageLike = string | { message?: string };
type EvidenceGapLike = string | { type?: string };
type ClarificationQuestionLike = string | { question?: string };

export function useSendMessage(caseId: string) {
  const addMessage = useChatStore((state) => state.addMessage);

  return useMutation({
    mutationFn: (message: string) => sendChatMessage(caseId, message),
    onSuccess: (response) => {
      console.log('[Chat] API response:', JSON.stringify(response?.data, null, 2));

      const data = response?.data;
      if (!data) {
        console.error('[Chat] No response data received');
        addMessage(caseId, {
          id: Date.now().toString(),
          role: 'assistant',
          content: '抱歉，服务器返回了空响应。',
          timestamp: new Date().toISOString(),
        });
        return;
      }

      const content = data.answer || data.content || '';
      const suggestions = data.suggestions || [];
      const evidenceGaps = data.evidence_gaps || [];
      const evidenceSuggestions = data.evidence_suggestions || [];
      const needsClarification = data.needs_clarification || false;
      const clarificationQuestions = data.clarification_questions || [];

      if (!content && suggestions.length === 0 && evidenceGaps.length === 0) {
        console.warn('[Chat] Empty response - no answer, suggestions, or gaps');
      }

      let displayContent = content;
      if (suggestions.length > 0) {
        displayContent += '\n\n💡 建议操作：\n' + (suggestions as MessageLike[]).map((s, i: number) => `${i + 1}. ${typeof s === 'string' ? s : s.message || ''}`).join('\n');
      }
      if (evidenceGaps.length > 0) {
        displayContent += '\n\n⚠️ 证据缺口：\n' + (evidenceGaps as EvidenceGapLike[]).map((g, i: number) => `${i + 1}. ${typeof g === 'string' ? g : g.type || ''}`).join('\n');
      }
      if (evidenceSuggestions.length > 0) {
        displayContent += '\n\n📋 证据建议：\n' + evidenceSuggestions.map((s: string, i: number) => `${i + 1}. ${s}`).join('\n');
      }
      if (needsClarification && clarificationQuestions.length > 0) {
        displayContent += '\n\n❓ 需要补充信息：\n' + (clarificationQuestions as ClarificationQuestionLike[]).map((q) => typeof q === 'string' ? q : q.question || '').join('\n');
      }

      if (!displayContent.trim()) {
        displayContent = 'AI 分析完成，但未生成具体内容。请尝试提出更明确的问题。';
      }

      console.log('[Chat] Adding assistant message:', displayContent.substring(0, 100) + '...');
      addMessage(caseId, {
        id: Date.now().toString(),
        role: 'assistant',
        content: displayContent,
        timestamp: new Date().toISOString(),
        intent: data.intent,
        clarificationNeeded: needsClarification,
      });
    },
    onError: (error: unknown) => {
      console.error('[Chat] Send message failed:', error);

      let errorMessage = '抱歉，发送消息时遇到错误。';
      if (error && typeof error === 'object') {
        const err = error as { message?: string; response?: { data?: { message?: string } } };
        if (err.message) {
          errorMessage = `发送失败：${err.message}`;
        } else if (err.response?.data?.message) {
          errorMessage = `服务器错误：${err.response.data.message}`;
        }
      }

      addMessage(caseId, {
        id: Date.now().toString(),
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date().toISOString(),
      });
    },
  });
}

export function useQuickActions(caseId: string) {
  return useQuery({
    queryKey: ['quick-actions', caseId],
    queryFn: () => getQuickActions(caseId),
    enabled: !!caseId,
  });
}
