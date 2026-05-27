import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const evidenceTypeVariants = cva('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', {
  variants: {
    type: {
      contract: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      receipt: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      letter: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      identity: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      communication: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
      witness: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      expert: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
      audio_video: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      other: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    },
  },
  defaultVariants: { type: 'other' },
});

interface Props extends VariantProps<typeof evidenceTypeVariants> { label: string; }

export function EvidenceTypeBadge({ label, type }: Props) {
  return <span className={cn(evidenceTypeVariants({ type }))}>{label}</span>;
}
