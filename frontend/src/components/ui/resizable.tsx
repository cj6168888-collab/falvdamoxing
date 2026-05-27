import { cn } from '@/lib/utils';
import { GripVertical } from 'lucide-react';
import type * as React from 'react';
import * as ResizablePrimitive from 'react-resizable-panels';

type ResizablePanelGroupProps = React.ComponentProps<typeof ResizablePrimitive.Group>;
type ResizableHandleProps = React.ComponentProps<typeof ResizablePrimitive.Separator> & {
  withHandle?: boolean;
};

const ResizablePanelGroup = ({
  className,
  orientation = 'horizontal',
  ...props
}: ResizablePanelGroupProps) => (
  <ResizablePrimitive.Group
    className={cn('flex h-full w-full', className)}
    orientation={orientation}
    data-panel-group-direction={orientation}
    {...props}
  />
);

const ResizablePanel = ResizablePrimitive.Panel;

const ResizableHandle = ({ withHandle, className, ...props }: ResizableHandleProps) => (
  <ResizablePrimitive.Separator
    className={cn(
      'relative flex w-px items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-1 aria-[orientation=horizontal]:h-px aria-[orientation=horizontal]:w-full aria-[orientation=horizontal]:after:left-0 aria-[orientation=horizontal]:after:h-1 aria-[orientation=horizontal]:after:w-full aria-[orientation=horizontal]:after:-translate-y-1/2 aria-[orientation=horizontal]:after:translate-x-0 [&[aria-orientation=horizontal]>div]:rotate-90',
      className,
    )}
    {...props}
  >
    {withHandle && (
      <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border">
        <GripVertical className="h-2.5 w-2.5" />
      </div>
    )}
  </ResizablePrimitive.Separator>
);

export { ResizablePanelGroup, ResizablePanel, ResizableHandle };
