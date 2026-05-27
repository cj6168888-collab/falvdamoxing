import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

const statusVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'bg-primary/10 text-primary hover:bg-primary/20',
        success: 'bg-green-500/10 text-green-700 dark:text-green-400 hover:bg-green-500/20',
        warning: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-500/20',
        danger: 'bg-red-500/10 text-red-700 dark:text-red-400 hover:bg-red-500/20',
        info: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 hover:bg-blue-500/20',
        neutral: 'bg-muted text-muted-foreground hover:bg-muted/80',
      },
      size: {
        sm: 'px-2 py-0 text-[10px]',
        md: 'px-2.5 py-0.5 text-xs',
        lg: 'px-3 py-1 text-sm',
      },
      dot: {
        true: '',
        false: '',
      },
    },
    compoundVariants: [
      {
        variant: 'success',
        dot: true,
        className: 'before:inline-block before:h-1.5 before:w-1.5 before:rounded-full before:bg-green-500',
      },
      {
        variant: 'warning',
        dot: true,
        className: 'before:inline-block before:h-1.5 before:w-1.5 before:rounded-full before:bg-yellow-500',
      },
      {
        variant: 'danger',
        dot: true,
        className: 'before:inline-block before:h-1.5 before:w-1.5 before:rounded-full before:bg-red-500',
      },
      {
        variant: 'info',
        dot: true,
        className: 'before:inline-block before:h-1.5 before:w-1.5 before:rounded-full before:bg-blue-500',
      },
      {
        variant: 'default',
        dot: true,
        className: 'before:inline-block before:h-1.5 before:w-1.5 before:rounded-full before:bg-primary',
      },
    ],
    defaultVariants: {
      variant: 'default',
      size: 'md',
      dot: false,
    },
  },
);

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusVariants> {
  label: string;
  disabled?: boolean;
}

const StatusBadge = React.forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ className, variant, size, dot, label, disabled, ...props }, ref) => {
    return (
      <span
        ref={ref}
        role="status"
        aria-disabled={disabled}
        aria-label={`状态：${label}`}
        className={cn(
          statusVariants({ variant, size, dot, className }),
          disabled && 'pointer-events-none opacity-50',
        )}
        {...props}
      >
        {label}
      </span>
    );
  },
);

StatusBadge.displayName = 'StatusBadge';

export { StatusBadge };
