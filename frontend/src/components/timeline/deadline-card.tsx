import { Card, CardContent } from '@/components/ui/card';
import { DeadlineCountdown } from '@/components/common/deadline-countdown';

interface Props { title: string; dueDate: string; daysRemaining: number; legalBasis?: string; }

export function DeadlineCard({ title, dueDate, daysRemaining, legalBasis }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-medium">{title}</p>
            {legalBasis && <p className="text-xs text-muted-foreground">{legalBasis}</p>}
          </div>
          <DeadlineCountdown dueDate={dueDate} daysRemaining={daysRemaining} />
        </div>
      </CardContent>
    </Card>
  );
}
