import { renderHook, act } from '@testing-library/react';
import { useLayoutStore } from './layout.store';

vi.mock('zustand/middleware', async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    persist: (creator: unknown) => creator,
  };
});

describe('useLayoutStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useLayoutStore.setState({ panelSizes: {} });
  });

  it('initializes with empty panelSizes', () => {
    const { result } = renderHook(() => useLayoutStore());
    expect(result.current.panelSizes).toEqual({});
  });

  it('sets panel sizes for a key', () => {
    const { result } = renderHook(() => useLayoutStore());
    act(() => {
      result.current.setPanelSizes('case-detail', [50, 50]);
    });
    expect(result.current.panelSizes['case-detail']).toEqual([50, 50]);
  });

  it('gets panel sizes for a key', () => {
    const { result } = renderHook(() => useLayoutStore());
    act(() => {
      result.current.setPanelSizes('case-detail', [30, 70]);
    });
    expect(result.current.getPanelSizes('case-detail')).toEqual([30, 70]);
  });

  it('returns undefined for non-existent key', () => {
    const { result } = renderHook(() => useLayoutStore());
    expect(result.current.getPanelSizes('non-existent')).toBeUndefined();
  });

  it('stores multiple panel size configs', () => {
    const { result } = renderHook(() => useLayoutStore());
    act(() => {
      result.current.setPanelSizes('case-detail', [50, 50]);
      result.current.setPanelSizes('evidence', [30, 70]);
    });
    expect(Object.keys(result.current.panelSizes)).toHaveLength(2);
    expect(result.current.panelSizes['case-detail']).toEqual([50, 50]);
    expect(result.current.panelSizes['evidence']).toEqual([30, 70]);
  });
});
