import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
const chipVariants = cva('inline-flex items-center rounded-full px-3 py-1 text-xs font-medium', { variants: { variant: { default: 'bg-primary/10 text-primary', destructive: 'bg-destructive/10 text-destructive', outline: 'border border-border' } }, defaultVariants: { variant: 'default' } });
export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof chipVariants> {}
export function Chip({ className, variant, ...props }: ChipProps) { return <span className={cn(chipVariants({ variant }), className)} {...props} />; }
