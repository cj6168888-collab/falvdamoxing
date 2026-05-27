import { renderHook, act } from '@testing-library/react';
import { useUIStore } from './ui.store';

describe('useUIStore', () => {
  beforeEach(() => {
    useUIStore.setState({ sidebarCollapsed: false, theme: 'system' });
  });

  it('initializes with default values', () => {
    const { result } = renderHook(() => useUIStore());
    expect(result.current.sidebarCollapsed).toBe(false);
    expect(result.current.theme).toBe('system');
  });

  it('toggles sidebar', () => {
    const { result } = renderHook(() => useUIStore());
    act(() => {
      result.current.toggleSidebar();
    });
    expect(result.current.sidebarCollapsed).toBe(true);

    act(() => {
      result.current.toggleSidebar();
    });
    expect(result.current.sidebarCollapsed).toBe(false);
  });

  it('sets theme', () => {
    const { result } = renderHook(() => useUIStore());
    act(() => {
      result.current.setTheme('dark');
    });
    expect(result.current.theme).toBe('dark');
  });
});
