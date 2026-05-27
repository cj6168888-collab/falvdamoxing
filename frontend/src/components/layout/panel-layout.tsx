import { useState, useCallback, useEffect } from 'react';
import { Group, Panel, Separator, type Layout as ResizableLayout } from 'react-resizable-panels';
import { Layout, Monitor, Focus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLocalStorage } from '@/hooks/use-local-storage';

export type LayoutPreset = 'split' | 'focus' | 'fullscreen';
export type LayoutDirection = 'horizontal' | 'vertical';

interface PanelLayoutProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultLeftSize?: number;
  minLeftSize?: number;
  minRightSize?: number;
  storageKey?: string;
}

interface LayoutConfig {
  preset: LayoutPreset;
  direction: LayoutDirection;
  leftSize: number;
}

const LAYOUT_CONFIGS: Record<LayoutPreset, LayoutConfig> = {
  split: { preset: 'split', direction: 'horizontal', leftSize: 50 },
  focus: { preset: 'focus', direction: 'horizontal', leftSize: 70 },
  fullscreen: { preset: 'fullscreen', direction: 'horizontal', leftSize: 100 },
};

export function PanelLayout({
  left,
  right,
  defaultLeftSize = 50,
  minLeftSize = 20,
  minRightSize = 20,
  storageKey = 'panel-layout-config',
}: PanelLayoutProps) {
  const [savedConfig, setSavedConfig] = useLocalStorage<LayoutConfig>(storageKey, {
    preset: 'split',
    direction: 'horizontal',
    leftSize: defaultLeftSize,
  });

  const [currentConfig, setCurrentConfig] = useState<LayoutConfig>(savedConfig);

  useEffect(() => {
    setCurrentConfig(savedConfig);
  }, [savedConfig]);

  const handleLayoutChange = useCallback((layout: ResizableLayout) => {
    const sizes = Object.values(layout);
    if (sizes.length === 0) return;
    setCurrentConfig((prev) => ({
      ...prev,
      leftSize: sizes[0],
    }));
  }, []);

  const applyPreset = useCallback((preset: LayoutPreset) => {
    const config = LAYOUT_CONFIGS[preset];
    setCurrentConfig(config);
    setSavedConfig(config);
  }, [setSavedConfig]);

  const resetLayout = useCallback(() => {
    const defaultConfig: LayoutConfig = {
      preset: 'split',
      direction: 'horizontal',
      leftSize: defaultLeftSize,
    };
    setCurrentConfig(defaultConfig);
    setSavedConfig(defaultConfig);
  }, [defaultLeftSize, setSavedConfig]);

  // Fullscreen mode - only show one panel
  if (currentConfig.preset === 'fullscreen') {
    return (
      <div className="flex h-full">
        <div className="h-full w-full overflow-auto">{left}</div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Layout Controls Bar */}
      <div className="flex items-center justify-between border-b bg-background px-2 py-1.5">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => applyPreset('split')}
            className={currentConfig.preset === 'split' ? 'bg-accent' : ''}
            title="分屏模式"
          >
            <Layout className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => applyPreset('focus')}
            className={currentConfig.preset === 'focus' ? 'bg-accent' : ''}
            title="专注模式"
          >
            <Monitor className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => applyPreset('fullscreen')}
            className={(currentConfig.preset as LayoutPreset) === 'fullscreen' ? 'bg-accent' : ''}
            title="全屏模式"
          >
            <Focus className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {Math.round(currentConfig.leftSize)}% | {Math.round(100 - currentConfig.leftSize)}%
          </span>
          <Button variant="ghost" size="sm" onClick={resetLayout} className="text-xs">
            重置
          </Button>
        </div>
      </div>

      {/* Resizable Panels */}
      <div className="flex-1 overflow-hidden">
        <Group orientation={currentConfig.direction} onLayoutChange={handleLayoutChange}>
          <Panel defaultSize={currentConfig.leftSize} minSize={minLeftSize} className="overflow-auto">
            {left}
          </Panel>
          <Separator className="w-2 bg-border hover:bg-primary/20 transition-colors cursor-col-resize flex items-center justify-center">
            <div className="h-8 w-1 rounded-full bg-muted-foreground/30" />
          </Separator>
          <Panel defaultSize={100 - currentConfig.leftSize} minSize={minRightSize} className="overflow-auto">
            {right}
          </Panel>
        </Group>
      </div>
    </div>
  );
}

// Vertical Panel Layout for stacked content
interface VerticalPanelLayoutProps {
  top: React.ReactNode;
  bottom: React.ReactNode;
  defaultTopSize?: number;
  minTopSize?: number;
  minBottomSize?: number;
  storageKey?: string;
}

export function VerticalPanelLayout({
  top,
  bottom,
  defaultTopSize = 50,
  minTopSize = 20,
  minBottomSize = 20,
  storageKey = 'vertical-panel-layout',
}: VerticalPanelLayoutProps) {
  const [savedConfig] = useLocalStorage<LayoutConfig>(storageKey, {
    preset: 'split',
    direction: 'vertical',
    leftSize: defaultTopSize,
  });

  const [currentConfig, setCurrentConfig] = useState<LayoutConfig>(savedConfig);

  useEffect(() => {
    setCurrentConfig(savedConfig);
  }, [savedConfig]);

  const handleLayoutChange = useCallback((layout: ResizableLayout) => {
    const sizes = Object.values(layout);
    if (sizes.length === 0) return;
    setCurrentConfig((prev) => ({
      ...prev,
      leftSize: sizes[0],
    }));
  }, []);

  return (
    <div className="flex h-full flex-col">
      <Group orientation="vertical" onLayoutChange={handleLayoutChange}>
        <Panel defaultSize={currentConfig.leftSize} minSize={minTopSize} className="overflow-auto">
          {top}
        </Panel>
        <Separator className="h-2 bg-border hover:bg-primary/20 transition-colors cursor-row-resize flex items-center justify-center">
          <div className="h-1 w-8 rounded-full bg-muted-foreground/30" />
        </Separator>
        <Panel defaultSize={100 - currentConfig.leftSize} minSize={minBottomSize} className="overflow-auto">
          {bottom}
        </Panel>
      </Group>
    </div>
  );
}
