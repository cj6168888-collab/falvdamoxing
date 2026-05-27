import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';
import { StatusBadge, type StatusBadgeProps } from './status-badge';

const meta = {
  title: 'UI/StatusBadge',
  component: StatusBadge,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Status badge component for displaying case, item, evidence status labels.

## Features
- 6 color variants: default, success, warning, danger, info, neutral
- 3 sizes: sm, md, lg
- Status dot indicator
- Disabled state
- Dark mode support
- Accessibility (aria-* attributes)
- Hover state feedback

## Use Cases
- Case status: active, closed, archived
- Urgency: critical, warning, normal
- Evidence credibility: high, medium, low
- Deadline status: expired, upcoming, normal
        `,
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'danger', 'info', 'neutral'],
      description: 'Color variant',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size',
    },
    dot: {
      control: 'boolean',
      description: 'Show status dot',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    label: {
      control: 'text',
      description: 'Badge text',
    },
  },
  args: {
    label: 'Active',
    variant: 'success',
    size: 'md',
    dot: true,
    disabled: false,
  },
  tags: ['autodocs'],
} satisfies Meta<typeof StatusBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: 'Active',
    variant: 'success',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="mb-2 text-sm font-medium text-muted-foreground">Color Variants</h3>
        <div className="flex flex-wrap gap-2">
          <StatusBadge label="Default" variant="default" dot />
          <StatusBadge label="Success" variant="success" dot />
          <StatusBadge label="Warning" variant="warning" dot />
          <StatusBadge label="Danger" variant="danger" dot />
          <StatusBadge label="Info" variant="info" dot />
          <StatusBadge label="Neutral" variant="neutral" />
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-muted-foreground">Case Status</h3>
        <div className="flex flex-wrap gap-2">
          <StatusBadge label="Preparing" variant="neutral" dot />
          <StatusBadge label="Negotiating" variant="info" dot />
          <StatusBadge label="Litigation" variant="warning" dot />
          <StatusBadge label="Appeal" variant="danger" dot />
          <StatusBadge label="Execution" variant="default" dot />
          <StatusBadge label="Closed" variant="success" dot />
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-muted-foreground">Urgency Level</h3>
        <div className="flex flex-wrap gap-2">
          <StatusBadge label="Expired" variant="danger" dot />
          <StatusBadge label="Within 7 days" variant="warning" dot />
          <StatusBadge label="Within 30 days" variant="info" dot />
          <StatusBadge label="Future" variant="success" dot />
        </div>
      </div>
    </div>
  ),
};

export const WithDots: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <StatusBadge label="With dot" variant="success" dot />
      <StatusBadge label="No dot" variant="success" />
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <StatusBadge label="Small" variant="info" size="sm" />
      <StatusBadge label="Medium" variant="info" size="md" />
      <StatusBadge label="Large" variant="info" size="lg" />
    </div>
  ),
};

export const Disabled: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <StatusBadge label="Disabled success" variant="success" dot disabled />
      <StatusBadge label="Disabled warning" variant="warning" dot disabled />
      <StatusBadge label="Disabled danger" variant="danger" dot disabled />
    </div>
  ),
};

export const HoverStates: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">Hover to see background color change</p>
      <div className="flex flex-wrap gap-2">
        <StatusBadge label="Hover (default)" variant="default" dot />
        <StatusBadge label="Hover (success)" variant="success" dot />
        <StatusBadge label="Hover (warning)" variant="warning" dot />
        <StatusBadge label="Hover (danger)" variant="danger" dot />
        <StatusBadge label="Hover (info)" variant="info" dot />
        <StatusBadge label="Hover (neutral)" variant="neutral" />
      </div>
    </div>
  ),
};

export const InteractiveDemo: Story = {
  render: () => {
    const InteractiveStatusBadge = () => {
      const [variant, setVariant] = useState<StatusBadgeProps['variant']>('success');
      const [size, setSize] = useState<StatusBadgeProps['size']>('md');
      const [dot, setDot] = useState(true);
      const [disabled, setDisabled] = useState(false);

      const variants: NonNullable<StatusBadgeProps['variant']>[] = [
        'default',
        'success',
        'warning',
        'danger',
        'info',
        'neutral',
      ];
      const sizes: NonNullable<StatusBadgeProps['size']>[] = ['sm', 'md', 'lg'];

      return (
        <div className="flex flex-col gap-6">
          <StatusBadge
            label="Interactive Demo"
            variant={variant}
            size={size}
            dot={dot}
            disabled={disabled}
          />

          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2">
              {variants.map((v) => (
                <button
                  key={v}
                  onClick={() => setVariant(v)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    variant === v
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              {sizes.map((s) => (
                <button
                  key={s}
                  onClick={() => setSize(s)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    size === s
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={dot}
                  onChange={(e) => setDot(e.target.checked)}
                  className="rounded border-border"
                />
                Show dot
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={disabled}
                  onChange={(e) => setDisabled(e.target.checked)}
                  className="rounded border-border"
                />
                Disabled
              </label>
            </div>
          </div>
        </div>
      );
    };

    return <InteractiveStatusBadge />;
  },
};
