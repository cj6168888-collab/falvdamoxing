import { Button } from '@/components/ui/button';

interface Props { questions: string[]; onSelect: (q: string) => void; }

export function QuickQuestions({ questions, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q) => (
        <Button key={q} variant="outline" size="sm" onClick={() => onSelect(q)}>{q}</Button>
      ))}
    </div>
  );
}
