import { Card, CardContent } from '@/components/ui/card';
import { Scale } from 'lucide-react';

interface Props { title: string; status: string; amount?: number; onClick: () => void; }

export function CounterClaimCard({ title, status, amount, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-muted-foreground" />
          <p className="font-medium">{title}</p>
        </div>
        <p className="text-sm text-muted-foreground mt-1">{status}{amount != null ? ' · ¥' + amount.toLocaleString() : ''}</p>
      </CardContent>
    </Card>
  );
}
