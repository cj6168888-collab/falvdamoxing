import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Mic, Square } from 'lucide-react';

interface Props { onResult: (text: string) => void; }

export function SpeechToText({ onResult: _onResult }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>语音转文字</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-center">
          <Button onClick={() => setIsRecording(!isRecording)} variant={isRecording ? 'destructive' : 'default'}>
            {isRecording ? <><Square className="mr-2 h-4 w-4" />停止</> : <><Mic className="mr-2 h-4 w-4" />开始录音</>}
          </Button>
        </div>
        {transcript && <div className="rounded border p-4 max-h-48 overflow-y-auto"><p className="text-sm whitespace-pre-wrap">{transcript}</p></div>}
      </CardContent>
    </Card>
  );
}
