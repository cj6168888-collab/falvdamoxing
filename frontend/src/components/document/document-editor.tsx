import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { AutoSaveIndicator } from '@/components/common/auto-save-indicator';

interface Props { content: string; onSave: (content: string) => void; }

export function DocumentEditor({ content, onSave }: Props) {
  const [text, setText] = useState(content);
  return (
    <div className="space-y-4">
      <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={20} className="font-mono" />
      <div className="flex justify-between items-center">
        <AutoSaveIndicator status="saved" lastSaved={new Date()} />
        <Button onClick={() => onSave(text)}>保存</Button>
      </div>
    </div>
  );
}
