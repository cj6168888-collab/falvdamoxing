import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Props {
  questions: string[];
  onAnswer: (index: number, answer: string) => void;
  onSkip: () => void;
}

export function ClarificationPanel({ questions, onAnswer, onSkip }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>澄清问题</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {questions.map((q, i) => (
          <div key={i}>
            <p className="text-sm font-medium">{q}</p>
            <div className="flex gap-2 mt-1">
              <Button size="sm" onClick={() => onAnswer(i, '是')}>是</Button>
              <Button size="sm" variant="outline" onClick={() => onAnswer(i, '否')}>否</Button>
              <Button size="sm" variant="ghost" onClick={() => onAnswer(i, '不确定')}>不确定</Button>
            </div>
          </div>
        ))}
        <Button variant="ghost" size="sm" onClick={onSkip}>跳过直接分析</Button>
      </CardContent>
    </Card>
  );
}
