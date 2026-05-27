import { ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Item { label: string; href?: string; }
interface Props { items: Item[]; }

export function Breadcrumb({ items }: Props) {
  return (
    <nav className="flex items-center text-sm text-muted-foreground">
      {items.map((item, i) => (
        <span key={i} className="flex items-center">
          {i > 0 && <ChevronRight className="h-4 w-4 mx-1" />}
          {item.href ? <Link to={item.href} className="hover:text-foreground">{item.label}</Link> : <span>{item.label}</span>}
        </span>
      ))}
    </nav>
  );
}
