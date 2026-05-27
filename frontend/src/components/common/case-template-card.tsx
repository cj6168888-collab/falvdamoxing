import { FileText } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface Props { type: string; label: string; fields: string[]; evidence: string[]; documents: string[]; onSelect: () => void; }

export function CaseTemplateCard({ label, fields, evidence, documents, onSelect }: Props) {
  return (
    <Card className="cursor-pointer transition-shadow hover:shadow-md" onClick={onSelect}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">{label}</h3>
        </div>
        <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
          <li>预填字段: {fields.join(', ')}</li>
          <li>推荐证据: {evidence.slice(0, 2).join(', ')}...</li>
          <li>推荐文书: {documents.join(', ')}</li>
        </ul>
        <button className="mt-3 w-full rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90">选择</button>
      </CardContent>
    </Card>
  );
}
