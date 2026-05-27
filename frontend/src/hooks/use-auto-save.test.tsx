import { renderHook, act } from '@testing-library/react';
import { useAutoSave } from './use-auto-save';

describe('useAutoSave', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('initializes with null lastSaved and false isSaving', () => {
    const { result } = renderHook(() => useAutoSave('test-key'));

    expect(result.current.lastSaved).toBeNull();
    expect(result.current.isSaving).toBe(false);
  });

  it('saves content to localStorage with correct key', async () => {
    const { result } = renderHook(() => useAutoSave('doc-1'));

    await act(async () => {
      await result.current.save('test content');
    });

    const stored = localStorage.getItem('draft-doc-1');
    expect(stored).not.toBeNull();
    const parsed = JSON.parse(stored!);
    expect(parsed.content).toBe('test content');
    expect(parsed.timestamp).toBeDefined();
  });

  it('updates lastSaved after save', async () => {
    const { result } = renderHook(() => useAutoSave('doc-2'));

    expect(result.current.lastSaved).toBeNull();

    await act(async () => {
      await result.current.save('content');
    });

    expect(result.current.lastSaved).toBeInstanceOf(Date);
  });

  it('uses different keys for different hooks', async () => {
    const { result: r1 } = renderHook(() => useAutoSave('key-1'));
    const { result: r2 } = renderHook(() => useAutoSave('key-2'));

    await act(async () => {
      await r1.current.save('content 1');
    });
    await act(async () => {
      await r2.current.save('content 2');
    });

    const stored1 = JSON.parse(localStorage.getItem('draft-key-1')!);
    const stored2 = JSON.parse(localStorage.getItem('draft-key-2')!);
    expect(stored1.content).toBe('content 1');
    expect(stored2.content).toBe('content 2');
  });
});
