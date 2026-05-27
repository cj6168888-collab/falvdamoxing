import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Shield, Ban, AlertTriangle, Handshake } from 'lucide-react';

const TOOLS = [
  { icon: FileText, label: '申请执行', action: 'apply' },
  { icon: Shield, label: '财产保全', action: 'preserve' },
  { icon: Ban, label: '限制高消费', action: 'restrict' },
  { icon: AlertTriangle, label: '纳入失信', action: 'blacklist' },
  { icon: Handshake, label: '执行和解', action: 'settle' },
];

interface Props { onAction: (action: string) => void; }

export function ExecutionTools({ onAction }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>执行辅助工具</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {TOOLS.map((t) => (
            <Button key={t.action} variant="outline" className="flex items-center justify-center gap-2" onClick={() => onAction(t.action)}>
              <t.icon className="h-4 w-4" />{t.label}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
