import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface Props { role: 'user' | 'assistant' | 'system'; content: string; timestamp: string; }

export function ChatMessage({ role, content, timestamp }: Props) {
  return (
    <div className={cn('flex', role === 'user' ? 'justify-end' : 'justify-start')}>
      <Card className={cn('max-w-[80%]', role === 'user' ? 'bg-primary text-primary-foreground' : '')}>
        <CardContent className="p-3">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
          <p className={cn('text-xs mt-1', role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground')}>
            {timestamp}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
