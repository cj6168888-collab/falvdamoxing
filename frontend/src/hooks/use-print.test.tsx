import { renderHook, act } from '@testing-library/react';
import { usePrint } from './use-print';

describe('usePrint', () => {
  it('handlePrint calls window.print when no elementId provided', () => {
    const printSpy = vi.fn();
    vi.stubGlobal('print', printSpy);

    const { result } = renderHook(() => usePrint());

    act(() => {
      result.current.handlePrint();
    });

    expect(printSpy).toHaveBeenCalled();

    vi.unstubAllGlobals();
  });

  it('handlePrint opens print window when elementId is provided', () => {
    const element = document.createElement('div');
    element.id = 'print-content';
    element.innerHTML = '<p>Test content</p>';
    document.body.appendChild(element);

    const mockPrintWindow = {
      document: {
        write: vi.fn(),
        close: vi.fn(),
      },
      focus: vi.fn(),
      print: vi.fn(),
      close: vi.fn(),
    };

    vi.spyOn(window, 'open').mockReturnValue(mockPrintWindow as unknown as Window);

    const { result } = renderHook(() => usePrint());

    act(() => {
      result.current.handlePrint('print-content');
    });

    expect(window.open).toHaveBeenCalledWith('', '_blank');
    expect(mockPrintWindow.document.write).toHaveBeenCalled();
    expect(mockPrintWindow.document.close).toHaveBeenCalled();
    expect(mockPrintWindow.focus).toHaveBeenCalled();
    expect(mockPrintWindow.print).toHaveBeenCalled();
    expect(mockPrintWindow.close).toHaveBeenCalled();

    vi.restoreAllMocks();
  });

  it('print window receives element content', () => {
    const element = document.createElement('div');
    element.id = 'my-element';
    element.innerHTML = '<h1>Hello World</h1>';
    document.body.appendChild(element);

    const mockPrintWindow = {
      document: {
        write: vi.fn(),
        close: vi.fn(),
      },
      focus: vi.fn(),
      print: vi.fn(),
      close: vi.fn(),
    };

    vi.spyOn(window, 'open').mockReturnValue(mockPrintWindow as unknown as Window);

    const { result } = renderHook(() => usePrint());

    act(() => {
      result.current.handlePrint('my-element');
    });

    const writtenContent = mockPrintWindow.document.write.mock.calls[0][0];
    expect(writtenContent).toContain('<h1>Hello World</h1>');

    vi.restoreAllMocks();
  });

  it('does nothing when elementId is not found', () => {
    const openSpy = vi.spyOn(window, 'open').mockReturnValue(null);

    const { result } = renderHook(() => usePrint());

    act(() => {
      result.current.handlePrint('non-existent-element');
    });

    expect(openSpy).not.toHaveBeenCalled();

    vi.restoreAllMocks();
  });

  it('does nothing when window.open returns null', () => {
    const element = document.createElement('div');
    element.id = 'print-me';
    document.body.appendChild(element);

    vi.spyOn(window, 'open').mockReturnValue(null);

    const { result } = renderHook(() => usePrint());

    act(() => {
      result.current.handlePrint('print-me');
    });

    vi.restoreAllMocks();
  });
});
