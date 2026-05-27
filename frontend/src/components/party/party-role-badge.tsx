import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const partyRoleVariants = cva('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', {
  variants: {
    role: {
      plaintiff: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      defendant: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      third_party: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      counter_claimant: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      counter_defendant: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    },
  },
  defaultVariants: { role: 'plaintiff' },
});

interface Props extends VariantProps<typeof partyRoleVariants> { label: string; }

export function PartyRoleBadge({ label, role }: Props) {
  return <span className={cn(partyRoleVariants({ role }))}>{label}</span>;
}
