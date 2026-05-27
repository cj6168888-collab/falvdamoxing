import { Card, CardContent } from '@/components/ui/card';
import { User } from 'lucide-react';

interface Props { name: string; role: string; phone?: string; onClick: () => void; }

export function PartyCard({ name, role, phone, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <User className="h-5 w-5 text-muted-foreground" />
          <div>
            <p className="font-medium">{name}</p>
            <p className="text-sm text-muted-foreground">{role}{phone ? ' · ' + phone : ''}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
