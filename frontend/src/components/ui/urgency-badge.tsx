import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export interface UrgencyBadgeProps {
  daysRemaining: number;
  label?: string;
  className?: string;
}

type UrgencyLevel = 'expired' | 'urgent' | 'warning' | 'normal';

function getUrgencyLevel(daysRemaining: number): UrgencyLevel {
  if (daysRemaining < 0) return 'expired';
  if (daysRemaining <= 7) return 'urgent';
  if (daysRemaining <= 30) return 'warning';
  return 'normal';
}

const urgencyConfig: Record<
  UrgencyLevel,
  {
    label: string;
    bgClass: string;
    textClass: string;
    darkBgClass: string;
    darkTextClass: string;
  }
> = {
  expired: {
    label: '过期',
    bgClass: 'bg-[#DC2626]',
    textClass: 'text-white',
    darkBgClass: 'dark:bg-[#DC2626]',
    darkTextClass: 'dark:text-white',
  },
  urgent: {
    label: '紧急',
    bgClass: 'bg-[#F59E0B]',
    textClass: 'text-white',
    darkBgClass: 'dark:bg-[#F59E0B]',
    darkTextClass: 'dark:text-white',
  },
  warning: {
    label: '预警',
    bgClass: 'bg-[#FEF08A]',
    textClass: 'text-yellow-900',
    darkBgClass: 'dark:bg-[#FEF08A]/20',
    darkTextClass: 'dark:text-[#FEF08A]',
  },
  normal: {
    label: '正常',
    bgClass: 'bg-transparent',
    textClass: 'text-[#16A34A]',
    darkBgClass: 'dark:bg-transparent',
    darkTextClass: 'dark:text-[#16A34A]',
  },
};

export function UrgencyBadge({ daysRemaining, label, className }: UrgencyBadgeProps) {
  const level = getUrgencyLevel(daysRemaining);
  const config = urgencyConfig[level];
  const displayLabel = label ?? config.label;

  const baseClasses = cn(
    'inline-flex items-center justify-center rounded-md px-2 py-0.5 text-xs font-semibold transition-colors',
    config.bgClass,
    config.textClass,
    config.darkBgClass,
    config.darkTextClass,
    className,
  );

  const daysText =
    level === 'expired'
      ? `已过期 ${Math.abs(daysRemaining)} 天`
      : `剩余 ${daysRemaining} 天`;

  if (level === 'expired') {
    return (
      <motion.span
        className={baseClasses}
        animate={{ opacity: [1, 0.6, 1] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        role="status"
        aria-label={`紧迫度: ${displayLabel}, ${daysText}`}
      >
        {displayLabel}
      </motion.span>
    );
  }

  return (
    <span
      className={baseClasses}
      role="status"
      aria-label={`紧迫度: ${displayLabel}, ${daysText}`}
    >
      {displayLabel}
    </span>
  );
}
