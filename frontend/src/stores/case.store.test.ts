import { renderHook, act } from '@testing-library/react';
import { useCaseStore } from './case.store';
import type { Case } from '@/types/case.types';

const mockCase: Case = {
  id: 'case-1',
  title: 'Test Case',
  type: 'civil',
  status: 'litigating',
  plaintiff: { name: 'Plaintiff' },
  defendant: { name: 'Defendant' },
  evidenceCount: 0,
  documentCount: 0,
  deadlineCount: 0,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

describe('useCaseStore', () => {
  beforeEach(() => {
    useCaseStore.setState({ currentCase: null, selectedCases: [] });
  });

  it('initializes with default values', () => {
    const { result } = renderHook(() => useCaseStore());
    expect(result.current.currentCase).toBeNull();
    expect(result.current.selectedCases).toEqual([]);
  });

  it('sets current case', () => {
    const { result } = renderHook(() => useCaseStore());
    act(() => {
      result.current.setCurrentCase(mockCase);
    });
    expect(result.current.currentCase).toEqual(mockCase);
  });

  it('toggles selected case - add', () => {
    const { result } = renderHook(() => useCaseStore());
    act(() => {
      result.current.toggleSelectedCase('case-1');
    });
    expect(result.current.selectedCases).toEqual(['case-1']);
  });

  it('toggles selected case - remove', () => {
    const { result } = renderHook(() => useCaseStore());
    act(() => {
      result.current.toggleSelectedCase('case-1');
    });
    act(() => {
      result.current.toggleSelectedCase('case-1');
    });
    expect(result.current.selectedCases).toEqual([]);
  });

  it('clears all selected cases', () => {
    const { result } = renderHook(() => useCaseStore());
    act(() => {
      result.current.toggleSelectedCase('case-1');
      result.current.toggleSelectedCase('case-2');
    });
    expect(result.current.selectedCases).toHaveLength(2);
    act(() => {
      result.current.clearSelectedCases();
    });
    expect(result.current.selectedCases).toEqual([]);
  });
});
