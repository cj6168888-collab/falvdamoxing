import { Card, CardContent } from '@/components/ui/card';
import { Gavel } from 'lucide-react';

interface Props { evidenceName: string; authenticity: string; legality: string; relevance: string; }

export function CrossExamCard({ evidenceName, authenticity, legality, relevance }: Props) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Gavel className="h-4 w-4 text-muted-foreground" />
          <p className="font-medium">{evidenceName}</p>
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
          <div>真实性: {authenticity}</div>
          <div>合法性: {legality}</div>
          <div>关联性: {relevance}</div>
        </div>
      </CardContent>
    </Card>
  );
}
