import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ReactNode } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PanelLayout, VerticalPanelLayout } from '@/components/layout/panel-layout';

const SPLIT_TITLE = '\u5206\u5c4f\u6a21\u5f0f';
const FOCUS_TITLE = '\u4e13\u6ce8\u6a21\u5f0f';
const FULLSCREEN_TITLE = '\u5168\u5c4f\u6a21\u5f0f';
const RESET_TEXT = '\u91cd\u7f6e';

vi.mock('react-resizable-panels', () => ({
  Group: ({ children, orientation }: { children: ReactNode; orientation?: string; onLayoutChange?: () => void }) => (
    <div data-testid="panel-group" data-direction={orientation}>
      {children}
    </div>
  ),
  Panel: ({ children, defaultSize, minSize, className }: { children: ReactNode; defaultSize?: number; minSize?: number; className?: string }) => (
    <div data-testid="panel" data-size={defaultSize} data-minsize={minSize} className={className}>
      {children}
    </div>
  ),
  Separator: ({ children, className }: { children?: ReactNode; className?: string }) => (
    <div data-testid="panel-resize-handle" className={className}>
      {children || <div />}
    </div>
  ),
}));

describe('PanelLayout', () => {
  const leftContent = <div data-testid="left-panel">Left Content</div>;
  const rightContent = <div data-testid="right-panel">Right Content</div>;

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default split layout', () => {
    render(<PanelLayout left={leftContent} right={rightContent} />);

    expect(screen.getByTestId('panel-group')).toBeTruthy();
    expect(screen.getByTestId('left-panel')).toBeTruthy();
    expect(screen.getByTestId('right-panel')).toBeTruthy();
  });

  it('displays layout control buttons', () => {
    render(<PanelLayout left={leftContent} right={rightContent} />);

    expect(screen.getByTitle(SPLIT_TITLE)).toBeTruthy();
    expect(screen.getByTitle(FOCUS_TITLE)).toBeTruthy();
    expect(screen.getByTitle(FULLSCREEN_TITLE)).toBeTruthy();
  });

  it('displays current split percentage', () => {
    render(<PanelLayout left={leftContent} right={rightContent} defaultLeftSize={50} />);

    expect(screen.getByText(/\d+% \| \d+%/)).toBeTruthy();
  });

  it('applies split preset correctly', async () => {
    render(<PanelLayout left={leftContent} right={rightContent} />);

    fireEvent.click(screen.getByTitle(SPLIT_TITLE));

    await waitFor(() => {
      expect(screen.getByTestId('panel-group')).toBeTruthy();
    });
  });

  it('applies focus preset correctly', async () => {
    render(<PanelLayout left={leftContent} right={rightContent} />);

    fireEvent.click(screen.getByTitle(FOCUS_TITLE));

    await waitFor(() => {
      expect(screen.getByTestId('panel-group')).toBeTruthy();
    });
  });

  it('applies fullscreen preset correctly', async () => {
    render(<PanelLayout left={leftContent} right={rightContent} />);

    fireEvent.click(screen.getByTitle(FULLSCREEN_TITLE));

    await waitFor(() => {
      expect(screen.getByTestId('left-panel')).toBeTruthy();
    });
    expect(screen.queryByTestId('right-panel')).toBeNull();
  });

  it('resets layout to default', async () => {
    render(
      <PanelLayout
        left={leftContent}
        right={rightContent}
        defaultLeftSize={50}
        storageKey="test-layout"
      />
    );

    fireEvent.click(screen.getByText(RESET_TEXT));

    await waitFor(() => {
      expect(screen.getByText(/\d+% \| \d+%/)).toBeTruthy();
    });
  });

  it('persists layout to localStorage', () => {
    const { rerender } = render(
      <PanelLayout left={leftContent} right={rightContent} storageKey="persist-test" />
    );

    fireEvent.click(screen.getByTitle(FOCUS_TITLE));

    expect(localStorage.getItem('persist-test')).toBeTruthy();

    rerender(<PanelLayout left={leftContent} right={rightContent} storageKey="persist-test" />);
  });

  it('respects min size constraints', () => {
    render(
      <PanelLayout
        left={leftContent}
        right={rightContent}
        minLeftSize={30}
        minRightSize={40}
      />
    );

    const panels = screen.getAllByTestId('panel');
    expect(panels[0].getAttribute('data-minsize')).toBe('30');
    expect(panels[1].getAttribute('data-minsize')).toBe('40');
  });
});

describe('VerticalPanelLayout', () => {
  const topContent = <div data-testid="top-panel">Top Content</div>;
  const bottomContent = <div data-testid="bottom-panel">Bottom Content</div>;

  beforeEach(() => {
    localStorage.clear();
  });

  it('renders vertical panels', () => {
    render(<VerticalPanelLayout top={topContent} bottom={bottomContent} />);

    expect(screen.getByTestId('panel-group')).toBeTruthy();
    expect(screen.getByTestId('top-panel')).toBeTruthy();
    expect(screen.getByTestId('bottom-panel')).toBeTruthy();
  });

  it('has vertical direction', () => {
    render(<VerticalPanelLayout top={topContent} bottom={bottomContent} />);

    expect(screen.getByTestId('panel-group').getAttribute('data-direction')).toBe('vertical');
  });

  it('applies the default top size', () => {
    render(
      <VerticalPanelLayout
        top={topContent}
        bottom={bottomContent}
        defaultTopSize={60}
        storageKey="vertical-test"
      />
    );

    const panels = screen.getAllByTestId('panel');
    expect(panels[0].getAttribute('data-size')).toBe('60');
    expect(panels[1].getAttribute('data-size')).toBe('40');
  });
});

describe('Layout Persistence', () => {
  it('saves layout configuration to localStorage', () => {
    render(<PanelLayout left={<div>Left</div>} right={<div>Right</div>} storageKey="layout-persist" />);

    fireEvent.click(screen.getByTitle(FOCUS_TITLE));

    const savedConfig = localStorage.getItem('layout-persist');
    expect(savedConfig).toBeTruthy();

    const config = JSON.parse(savedConfig!);
    expect(config.preset).toBe('focus');
  });

  it('loads saved layout on mount', () => {
    localStorage.setItem('layout-load', JSON.stringify({
      preset: 'focus',
      direction: 'horizontal',
      leftSize: 70,
    }));

    render(<PanelLayout left={<div>Left</div>} right={<div>Right</div>} storageKey="layout-load" />);

    expect(screen.getByTitle(FOCUS_TITLE).className).toContain('bg-accent');
  });
});
