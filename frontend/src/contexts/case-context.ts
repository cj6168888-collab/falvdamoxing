import { createContext } from 'react';

export interface CaseContextType {
  currentCaseId: string | null;
  setCurrentCaseId: (id: string | null) => void;
}

export const CaseContext = createContext<CaseContextType | undefined>(undefined);
