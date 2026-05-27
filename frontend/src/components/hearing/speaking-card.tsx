import { Card, CardContent } from '@/components/ui/card';
import { Gavel } from 'lucide-react';

interface Props { title: string; content: string; }

export function SpeakingCard({ title, content }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Gavel className="h-4 w-4 text-primary" />
          <p className="font-medium">{title}</p>
        </div>
        <p className="text-sm text-muted-foreground mt-2 whitespace-pre-wrap">{content}</p>
      </CardContent>
    </Card>
  );
}
