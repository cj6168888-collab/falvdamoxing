import { create } from 'zustand';
import type { ProfileSummary } from '@/types/profile.types';

interface ProfileStore {
  profiles: Record<string, ProfileSummary>;
  setProfile: (caseId: string, profile: ProfileSummary) => void;
  getProfile: (caseId: string) => ProfileSummary | undefined;
}

export const useProfileStore = create<ProfileStore>((set, get) => ({
  profiles: {},
  setProfile: (caseId, profile) =>
    set((state) => ({
      profiles: { ...state.profiles, [caseId]: profile },
    })),
  getProfile: (caseId) => get().profiles[caseId],
}));
