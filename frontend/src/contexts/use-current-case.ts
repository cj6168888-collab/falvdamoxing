import { useContext } from 'react';
import { CaseContext } from './case-context';

export function useCurrentCase() {
  const context = useContext(CaseContext);
  if (!context) {
    throw new Error('useCurrentCase must be used within CaseProvider');
  }
  return context;
}
