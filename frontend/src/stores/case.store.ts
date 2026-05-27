import { create } from 'zustand';
import type { Case } from '@/types/case.types';

interface CaseStore {
  currentCase: Case | null;
  selectedCases: string[];
  setCurrentCase: (caseData: Case | null) => void;
  toggleSelectedCase: (caseId: string) => void;
  clearSelectedCases: () => void;
}

export const useCaseStore = create<CaseStore>((set) => ({
  currentCase: null,
  selectedCases: [],
  setCurrentCase: (caseData) => set({ currentCase: caseData }),
  toggleSelectedCase: (caseId) =>
    set((state) => ({
      selectedCases: state.selectedCases.includes(caseId)
        ? state.selectedCases.filter((id) => id !== caseId)
        : [...state.selectedCases, caseId],
    })),
  clearSelectedCases: () => set({ selectedCases: [] }),
}));
