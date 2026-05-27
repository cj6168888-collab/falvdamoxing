import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, Pause } from 'lucide-react';

interface Props { src: string; }

export function AudioPlayer({ src: _src }: Props) {
  const [isPlaying, setIsPlaying] = useState(false);
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <Button size="icon" onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <div className="flex-1 h-2 bg-muted rounded"><div className="h-2 bg-primary rounded" style={{ width: '30%' }} /></div>
          <span className="text-xs text-muted-foreground">00:00 / 00:00</span>
        </div>
      </CardContent>
    </Card>
  );
}
