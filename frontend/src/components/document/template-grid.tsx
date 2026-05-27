import { Card, CardContent } from '@/components/ui/card';
import { FileText } from 'lucide-react';

interface Template { id: string; name: string; category: string; }
interface Props { templates: Template[]; onSelect: (id: string) => void; }

export function TemplateGrid({ templates, onSelect }: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {templates.map((t) => (
        <Card key={t.id} className="cursor-pointer hover:shadow-md" onClick={() => onSelect(t.id)}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <div><p className="font-medium">{t.name}</p><p className="text-sm text-muted-foreground">{t.category}</p></div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
