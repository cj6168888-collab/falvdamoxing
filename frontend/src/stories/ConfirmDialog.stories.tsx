import type { Meta, StoryObj } from '@storybook/react-vite';
import { useCallback, useState } from 'react';
import { ConfirmDialog } from '@/components/common/confirm-dialog';

const meta = {
  title: 'Common/ConfirmDialog',
  component: ConfirmDialog,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'radio' },
      options: ['default', 'destructive'],
    },
    isLoading: {
      control: { type: 'boolean' },
    },
  },
} satisfies Meta<typeof ConfirmDialog>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    open: true,
    title: 'Archive Case',
    description: 'Are you sure you want to archive this case? It will be moved to the closed cases list but can still be viewed at any time.',
    confirmLabel: 'Archive',
    cancelLabel: 'Cancel',
    variant: 'default',
    isLoading: false,
    onConfirm: () => {},
    onOpenChange: () => {},
  },
  render: (args) => {
    const [open, setOpen] = useState(args.open ?? true);
    const [isLoading, setIsLoading] = useState(false);

    const handleConfirm = useCallback(async () => {
      setIsLoading(true);
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setIsLoading(false);
      setOpen(false);
    }, []);

    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
        >
          Open Archive Confirmation
        </button>
        <ConfirmDialog
          {...args}
          open={open}
          onOpenChange={setOpen}
          isLoading={isLoading}
          onConfirm={handleConfirm}
        />
      </div>
    );
  },
};

export const DeleteCase: Story = {
  args: {
    open: true,
    title: 'Delete Case',
    description: 'Are you sure you want to delete this loan dispute case? This will permanently delete the case and all associated data (evidence, documents, timeline). This action cannot be undone.',
    confirmLabel: 'Delete',
    cancelLabel: 'Cancel',
    variant: 'destructive',
    isLoading: false,
    onConfirm: () => {},
    onOpenChange: () => {},
  },
  render: (args) => {
    const [open, setOpen] = useState(args.open ?? true);
    const [isLoading, setIsLoading] = useState(false);

    const handleConfirm = useCallback(async () => {
      setIsLoading(true);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setIsLoading(false);
      setOpen(false);
    }, []);

    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-md bg-destructive px-4 py-2 text-sm text-destructive-foreground hover:bg-destructive/90"
        >
          Open Delete Confirmation
        </button>
        <ConfirmDialog
          {...args}
          open={open}
          onOpenChange={setOpen}
          isLoading={isLoading}
          onConfirm={handleConfirm}
        />
      </div>
    );
  },
};

export const DangerousOperation: Story = {
  args: {
    open: true,
    title: 'Clear All Case Data',
    description: 'Warning: This will clear all case data in the system, including case information, evidence materials, document drafts, and timeline records. This action is irreversible. Please confirm you have backed up important data.',
    confirmLabel: 'Confirm Clear',
    cancelLabel: 'Cancel',
    variant: 'destructive',
    isLoading: false,
    onConfirm: () => {},
    onOpenChange: () => {},
  },
  render: (args) => {
    const [open, setOpen] = useState(args.open ?? true);
    const [isLoading, setIsLoading] = useState(false);

    const handleConfirm = useCallback(async () => {
      setIsLoading(true);
      await new Promise((resolve) => setTimeout(resolve, 3000));
      setIsLoading(false);
      setOpen(false);
    }, []);

    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-md bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
        >
          Open Dangerous Operation Confirmation
        </button>
        <ConfirmDialog
          {...args}
          open={open}
          onOpenChange={setOpen}
          isLoading={isLoading}
          onConfirm={handleConfirm}
        />
      </div>
    );
  },
};
