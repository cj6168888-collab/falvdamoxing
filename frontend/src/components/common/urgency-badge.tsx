import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const urgencyBadgeVariants = cva('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium', {
  variants: {
    urgency: {
      expired: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      urgent: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      normal: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    },
  },
  defaultVariants: { urgency: 'normal' },
});

interface UrgencyBadgeProps extends VariantProps<typeof urgencyBadgeVariants> {
  daysRemaining: number;
}

export function UrgencyBadge({ daysRemaining, urgency }: UrgencyBadgeProps) {
  const label =
    daysRemaining < 0
      ? `已过期 ${Math.abs(daysRemaining)} 天`
      : daysRemaining === 0
        ? '今天到期'
        : `还剩 ${daysRemaining} 天`;

  return <span className={cn(urgencyBadgeVariants({ urgency }))}>{label}</span>;
}
