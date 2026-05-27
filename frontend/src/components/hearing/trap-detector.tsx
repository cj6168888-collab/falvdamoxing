import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AlertTriangle } from 'lucide-react';
import { useState } from 'react';

interface Result { type: string; suggestion: string; }
interface Props { onDetect: (content: string) => void; result?: Result; }

export function TrapDetector({ onDetect, result }: Props) {
  const [content, setContent] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" />法庭陷阱识别</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <Textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="输入对方发言..." rows={3} />
        <Button onClick={() => onDetect(content)}>检测</Button>
        {result && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20">
            <p className="font-medium text-red-700 dark:text-red-400">{result.type}</p>
            <p className="text-sm mt-1">{result.suggestion}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
