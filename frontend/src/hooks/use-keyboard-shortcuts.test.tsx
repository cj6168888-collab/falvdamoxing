import { renderHook, act } from '@/test/test-utils';
import { useKeyboardShortcuts } from './use-keyboard-shortcuts';

describe('useKeyboardShortcuts', () => {
  it('registers keyboard shortcuts and triggers action on key press', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 's', action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's' }));
    });

    expect(action).toHaveBeenCalledTimes(1);
  });

  it('handles ctrl modifier key', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 's', ctrl: true, action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }));
    });

    expect(action).toHaveBeenCalledTimes(1);
  });

  it('does not trigger when ctrl is required but not pressed', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 's', ctrl: true, action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's' }));
    });

    expect(action).not.toHaveBeenCalled();
  });

  it('handles shift modifier key', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'z', shift: true, action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', shiftKey: true }));
    });

    expect(action).toHaveBeenCalledTimes(1);
  });

  it('handles alt modifier key', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'f', alt: true, action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'f', altKey: true }));
    });

    expect(action).toHaveBeenCalledTimes(1);
  });

  it('handles combo keys with multiple modifiers', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 's', ctrl: true, shift: true, action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true, shiftKey: true }));
    });

    expect(action).toHaveBeenCalledTimes(1);
  });

  it('cleans up event listener on unmount', () => {
    const action = vi.fn();
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    const { unmount } = renderHook(() =>
      useKeyboardShortcuts([
        { key: 's', action },
      ])
    );

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
  });

  it('handles case-insensitive key matching', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 'S', action },
      ])
    );

    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 's' }));
    });

    expect(action).toHaveBeenCalledTimes(1);
  });

  it('calls preventDefault on matched shortcut', () => {
    const action = vi.fn();

    renderHook(() =>
      useKeyboardShortcuts([
        { key: 's', action },
      ])
    );

    const event = new KeyboardEvent('keydown', { key: 's' });
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault');

    act(() => {
      window.dispatchEvent(event);
    });

    expect(preventDefaultSpy).toHaveBeenCalledTimes(1);
  });
});
