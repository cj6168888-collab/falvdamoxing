import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface DraftStore {
  drafts: Record<string, { content: string; timestamp: number }>;
  saveDraft: (key: string, content: string) => void;
  getDraft: (key: string) => { content: string; timestamp: number } | null;
  clearDraft: (key: string) => void;
}

export const useDraftStore = create<DraftStore>()(
  persist(
    (set, get) => ({
      drafts: {},
      saveDraft: (key, content) =>
        set((state) => ({
          drafts: { ...state.drafts, [key]: { content, timestamp: Date.now() } },
        })),
      getDraft: (key) => get().drafts[key] || null,
      clearDraft: (key) =>
        set((state) => {
          const newDrafts = { ...state.drafts };
          delete newDrafts[key];
          return { drafts: newDrafts };
        }),
    }),
    { name: 'draft-storage' }
  )
);
