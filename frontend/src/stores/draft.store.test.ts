import { renderHook, act } from '@testing-library/react';
import { useDraftStore } from './draft.store';

describe('useDraftStore', () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset store state after localStorage clear
    useDraftStore.setState({ drafts: {} });
  });

  it('initializes with empty drafts', () => {
    const { result } = renderHook(() => useDraftStore());
    expect(result.current.drafts).toEqual({});
  });

  it('saves a draft', () => {
    const { result } = renderHook(() => useDraftStore());
    act(() => {
      result.current.saveDraft('doc-1', 'Test content');
    });
    const draft = result.current.getDraft('doc-1');
    expect(draft).not.toBeNull();
    expect(draft?.content).toBe('Test content');
  });

  it('returns null for non-existent draft', () => {
    const { result } = renderHook(() => useDraftStore());
    expect(result.current.getDraft('non-existent')).toBeNull();
  });

  it('clears a draft', () => {
    const { result } = renderHook(() => useDraftStore());
    act(() => {
      result.current.saveDraft('doc-1', 'Test content');
    });
    act(() => {
      result.current.clearDraft('doc-1');
    });
    expect(result.current.getDraft('doc-1')).toBeNull();
  });

  it('updates existing draft', () => {
    const { result } = renderHook(() => useDraftStore());
    act(() => {
      result.current.saveDraft('doc-1', 'First content');
    });
    act(() => {
      result.current.saveDraft('doc-1', 'Updated content');
    });
    const draft = result.current.getDraft('doc-1');
    expect(draft?.content).toBe('Updated content');
  });
});
