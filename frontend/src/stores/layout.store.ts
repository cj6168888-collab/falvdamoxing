import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface LayoutStore {
  panelSizes: Record<string, number[]>;
  setPanelSizes: (key: string, sizes: number[]) => void;
  getPanelSizes: (key: string) => number[] | undefined;
}

export const useLayoutStore = create<LayoutStore>()(
  persist(
    (set, get) => ({
      panelSizes: {},
      setPanelSizes: (key, sizes) =>
        set((state) => ({
          panelSizes: { ...state.panelSizes, [key]: sizes },
        })),
      getPanelSizes: (key) => get().panelSizes[key],
    }),
    { name: 'layout-storage' }
  )
);
