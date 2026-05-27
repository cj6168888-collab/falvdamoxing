import { cn } from '@/lib/utils';
interface MeterProps { value: number; max: number; className?: string; }
export function Meter({ value, max, className }: MeterProps) {
  const percentage = Math.min((value / max) * 100, 100);
  return (<div className={cn('h-2 w-full rounded-full bg-muted', className)}><div className="h-2 rounded-full bg-primary transition-all" style={{ width: percentage + '%' }} /></div>);
}
