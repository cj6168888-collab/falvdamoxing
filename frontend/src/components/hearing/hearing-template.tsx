import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

const TEMPLATES = ['开庭陈述', '举证提纲', '质证意见', '发问提纲', '辩论意见', '最后陈述'];

interface Props { onSelect: (template: string) => void; }

export function HearingTemplate({ onSelect }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>庭审文书模板</CardTitle></CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {TEMPLATES.map((t) => <Button key={t} variant="outline" onClick={() => onSelect(t)}><FileText className="mr-2 h-4 w-4" />{t}</Button>)}
      </CardContent>
    </Card>
  );
}
