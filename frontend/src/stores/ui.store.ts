import { create } from 'zustand';
import type { Theme } from '@/types/common.types';

interface UIStore {
  sidebarCollapsed: boolean;
  theme: Theme;
  toggleSidebar: () => void;
  setTheme: (theme: Theme) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarCollapsed: false,
  theme: 'system',
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setTheme: (theme) => set({ theme }),
}));
