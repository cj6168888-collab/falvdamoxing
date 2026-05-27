import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const statusBadgeVariants = cva('inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium', {
  variants: {
    variant: {
      completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      'in-progress': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      urgent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      draft: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
      closed: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500',
    },
  },
  defaultVariants: { variant: 'draft' },
});

interface StatusBadgeProps extends VariantProps<typeof statusBadgeVariants> {
  label: string;
}

export function StatusBadge({ label, variant }: StatusBadgeProps) {
  return <span className={cn(statusBadgeVariants({ variant }))}>{label}</span>;
}
