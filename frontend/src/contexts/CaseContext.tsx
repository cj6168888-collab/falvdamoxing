import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { CaseContext } from './case-context';

export function CaseProvider({ children }: { children: ReactNode }) {
  const [currentCaseId, setCurrentCaseId] = useState<string | null>(null);

  // 从localStorage恢复
  useEffect(() => {
    const saved = localStorage.getItem('current_case_id');
    if (saved) {
      setCurrentCaseId(saved);
    }
  }, []);

  // 保存到localStorage
  useEffect(() => {
    if (currentCaseId) {
      localStorage.setItem('current_case_id', currentCaseId);
    } else {
      localStorage.removeItem('current_case_id');
    }
  }, [currentCaseId]);

  return (
    <CaseContext.Provider value={{ currentCaseId, setCurrentCaseId }}>
      {children}
    </CaseContext.Provider>
  );
}
