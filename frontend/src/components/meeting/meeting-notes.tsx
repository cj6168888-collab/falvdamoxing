import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface Props { initialNotes?: string; onSave: (notes: string) => void; }

export function MeetingNotes({ initialNotes, onSave }: Props) {
  const [notes, setNotes] = useState(initialNotes || '');
  return (
    <Card>
      <CardHeader><CardTitle>会议纪要</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={10} placeholder="输入会议纪要..." />
        <Button onClick={() => onSave(notes)}>保存纪要</Button>
      </CardContent>
    </Card>
  );
}
