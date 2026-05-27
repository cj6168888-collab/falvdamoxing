import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const TYPES = ['商务谈判', '调解会议', '证据交换', '庭前会议'];

interface Props { onSelect: (type: string) => void; }

export function MeetingTemplate({ onSelect }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>会议类型</CardTitle></CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {TYPES.map((t) => <Button key={t} variant="outline" onClick={() => onSelect(t)}>{t}</Button>)}
      </CardContent>
    </Card>
  );
}
