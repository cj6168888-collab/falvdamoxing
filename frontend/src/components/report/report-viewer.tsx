import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface Props { title: string; content: string; onExport: (format: string) => void; }

export function ReportViewer({ title, content, onExport }: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{title}</CardTitle>
          <Button size="sm" variant="outline" onClick={() => onExport('pdf')}><Download className="mr-2 h-4 w-4" />导出</Button>
        </div>
      </CardHeader>
      <CardContent><div className="prose max-w-none whitespace-pre-wrap">{content}</div></CardContent>
    </Card>
  );
}
