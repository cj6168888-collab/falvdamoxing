import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { title: string; content: string; }

export function DocumentPreview({ title, content }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent><div className="prose max-w-none whitespace-pre-wrap">{content}</div></CardContent>
    </Card>
  );
}
