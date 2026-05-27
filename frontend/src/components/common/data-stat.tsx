import { formatNumber } from '@/lib/format';

interface DataStatProps {
  label: string;
  value: number | string;
  icon?: React.ElementType;
  trend?: { value: number; positive: boolean };
}

export function DataStat({ label, value, icon: Icon, trend }: DataStatProps) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{label}</p>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </div>
      <p className="mt-2 text-2xl font-bold">{typeof value === 'number' ? formatNumber(value) : value}</p>
      {trend && (
        <p className={`mt-1 text-xs ${trend.positive ? 'text-green-600' : 'text-red-600'}`}>
          {trend.positive ? '↑' : '↓'} {trend.value}%
        </p>
      )}
    </div>
  );
}
