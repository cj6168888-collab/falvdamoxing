import { Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

interface ExportPanelProps {
  title: string;
  formats: { label: string; ext: string }[];
  onExport: (format: string) => void;
}

export function ExportPanel({ title, formats, onExport }: ExportPanelProps) {
  return (
    <Dialog>
      <DialogTrigger asChild><Button variant="outline" size="sm"><Download className="mr-2 h-4 w-4" />导出</Button></DialogTrigger>
      <DialogContent aria-describedby={undefined}>
        <DialogHeader><DialogTitle>导出 {title}</DialogTitle></DialogHeader>
        <div className="grid grid-cols-2 gap-3">
          {formats.map((f) => (
            <Button key={f.ext} variant="outline" onClick={() => onExport(f.ext)} className="flex items-center justify-center gap-2">
              <FileText className="h-4 w-4" />{f.label} (. {f.ext})
            </Button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
