import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage } from '@/types/chat.types';

interface ChatStore {
  conversations: Record<string, ChatMessage[]>;
  addMessage: (caseId: string, message: ChatMessage) => void;
  clearConversation: (caseId: string) => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      conversations: {},
      addMessage: (caseId, message) =>
        set((state) => ({
          conversations: {
            ...state.conversations,
            [caseId]: [...(state.conversations[caseId] || []), message],
          },
        })),
      clearConversation: (caseId) =>
        set((state) => ({
          conversations: { ...state.conversations, [caseId]: [] },
        })),
    }),
    { name: 'chat-storage' }
  )
);
