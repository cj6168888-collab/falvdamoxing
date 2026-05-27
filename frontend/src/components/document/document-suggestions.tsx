import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lightbulb } from 'lucide-react';

interface Suggestion { type: string; reason: string; }
interface Props { suggestions: Suggestion[] | null | undefined; onGenerate: (type: string) => void; }

export function DocumentSuggestions({ suggestions, onGenerate }: Props) {
  if (!suggestions?.length) return null;
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><Lightbulb className="h-5 w-5 text-amber-500" />AI 推荐文书</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {suggestions.map((s, i) => (
          <div key={i} className="flex justify-between items-center p-3 rounded-lg border">
            <div><p className="font-medium">{s.type}</p><p className="text-sm text-muted-foreground">{s.reason}</p></div>
            <Button size="sm" onClick={() => onGenerate(s.type)}>生成</Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
