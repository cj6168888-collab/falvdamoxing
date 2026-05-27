import { renderHook, act } from '@/test/test-utils';
import { useVersionHistory } from './use-version-history';

describe('useVersionHistory', () => {
  it('addVersion creates new version', () => {
    const { result } = renderHook(() => useVersionHistory());

    act(() => {
      result.current.addVersion('first content');
    });

    expect(result.current.versions).toHaveLength(1);
    expect(result.current.versions[0]).toMatchObject({
      version: 1,
      content: 'first content',
    });
    expect(result.current.currentVersion).toBe(1);
  });

  it('getVersion retrieves correct version', () => {
    const { result } = renderHook(() => useVersionHistory());

    act(() => {
      result.current.addVersion('version 1');
      result.current.addVersion('version 2');
      result.current.addVersion('version 3');
    });

    const version2 = result.current.getVersion(2);
    expect(version2).toBeDefined();
    expect(version2?.content).toBe('version 2');
    expect(version2?.version).toBe(2);
  });

  it('revertToVersion restores content and updates currentVersion', () => {
    const { result } = renderHook(() => useVersionHistory());

    act(() => {
      result.current.addVersion('v1');
      result.current.addVersion('v2');
      result.current.addVersion('v3');
    });

    expect(result.current.currentVersion).toBe(3);

    act(() => {
      result.current.revertToVersion(1);
    });

    expect(result.current.currentVersion).toBe(1);
    expect(result.current.versions).toHaveLength(3);
  });

  it('versions list is maintained correctly', () => {
    const { result } = renderHook(() => useVersionHistory());

    act(() => {
      result.current.addVersion('content 1');
      result.current.addVersion('content 2');
    });

    expect(result.current.versions).toHaveLength(2);
    expect(result.current.versions[0].version).toBe(1);
    expect(result.current.versions[1].version).toBe(2);

    act(() => {
      result.current.addVersion('content 3');
    });

    expect(result.current.versions).toHaveLength(3);
    expect(result.current.versions[2].version).toBe(3);
  });

  it('currentVersion tracks correctly after multiple operations', () => {
    const { result } = renderHook(() => useVersionHistory());

    expect(result.current.currentVersion).toBe(0);

    act(() => {
      result.current.addVersion('first');
    });
    expect(result.current.currentVersion).toBe(1);

    act(() => {
      result.current.addVersion('second');
    });
    expect(result.current.currentVersion).toBe(2);

    act(() => {
      result.current.revertToVersion(1);
    });
    expect(result.current.currentVersion).toBe(1);
  });

  it('getVersion returns undefined for non-existent version', () => {
    const { result } = renderHook(() => useVersionHistory());

    act(() => {
      result.current.addVersion('only version');
    });

    const nonExistent = result.current.getVersion(99);
    expect(nonExistent).toBeUndefined();
  });
});
