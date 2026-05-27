import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mic, Square } from 'lucide-react';

interface Props { caseId: string; }

export function RealTimeAnalysis({ caseId: _caseId }: Props) {
  const [isListening, setIsListening] = useState(false);
  return (
    <Card>
      <CardHeader><CardTitle>实时分析</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-center">
          <Button onClick={() => setIsListening(!isListening)} variant={isListening ? 'destructive' : 'default'}>
            {isListening ? <><Square className="mr-2 h-4 w-4" />停止</> : <><Mic className="mr-2 h-4 w-4" />开始监听</>}
          </Button>
        </div>
        {isListening && <div className="h-32 rounded border p-4 overflow-y-auto"><p className="text-sm text-muted-foreground">监听中...</p></div>}
      </CardContent>
    </Card>
  );
}
