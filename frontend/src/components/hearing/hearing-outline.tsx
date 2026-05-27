import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Section { title: string; content: string; }
interface Props { sections: Section[]; }

export function HearingOutline({ sections }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>开庭提纲</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {sections.map((s, i) => (
          <div key={i}>
            <h4 className="font-medium">{s.title}</h4>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{s.content}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
