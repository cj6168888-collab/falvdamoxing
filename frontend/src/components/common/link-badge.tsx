import { Link } from 'lucide-react';

interface LinkBadgeProps {
  count: number;
  label: string;
  onClick?: () => void;
}

export function LinkBadge({ count, label, onClick }: LinkBadgeProps) {
  return (
    <button onClick={onClick} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground">
      <Link className="h-3 w-3" />
      <span>{label}</span>
      <span className="font-medium">{count}</span>
    </button>
  );
}
