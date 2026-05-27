import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

interface Item { name: string; formats: string[]; }
interface Props { items: Item[]; onExport: (item: string, format: string) => void; }

export function ExportMatrix({ items, onExport }: Props) {
  const formats = ['PDF', 'Word', 'Markdown', 'TXT'];
  return (
    <Card>
      <CardHeader><CardTitle>导出矩阵</CardTitle></CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr><th className="text-left p-2">内容</th>{formats.map((f) => <th key={f} className="p-2">{f}</th>)}</tr></thead>
            <tbody>{items.map((item) => (
              <tr key={item.name} className="border-t">
                <td className="p-2">{item.name}</td>
                {formats.map((f) => <td key={f} className="p-2"><Button size="sm" variant="outline" onClick={() => onExport(item.name, f)}><Download className="h-3 w-3" /></Button></td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
