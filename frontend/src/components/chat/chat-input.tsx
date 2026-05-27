import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';

interface Props { onSend: (message: string) => void; isLoading?: boolean; }

export function ChatInput({ onSend, isLoading }: Props) {
  const [message, setMessage] = useState('');
  const handleSend = () => {
    if (message.trim()) {
      onSend(message.trim());
      setMessage('');
    }
  };
  return (
    <div className="flex gap-2 p-4 border-t">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="输入您的问题..."
        className="flex-1"
        rows={2}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />
      <Button onClick={handleSend} disabled={isLoading} size="icon">
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
