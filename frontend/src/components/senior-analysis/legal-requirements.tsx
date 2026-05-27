import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Requirement { name: string; status: string; risk: string; description?: string; }
interface Props { requirements: Requirement[]; }

export function LegalRequirements({ requirements }: Props) {
  const iconMap: Record<string, React.ReactNode> = {
    met: <CheckCircle className="h-4 w-4 text-green-500" />,
    partial: <AlertCircle className="h-4 w-4 text-amber-500" />,
    unmet: <XCircle className="h-4 w-4 text-red-500" />,
  };
  return (
    <Card>
      <CardHeader><CardTitle>法律要件分析</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {requirements?.map((r, i) => (
          <div key={i} className="flex items-start gap-3">
            {iconMap[r.status] || iconMap.unmet}
            <div>
              <p className="font-medium">{r.name}</p>
              {r.description && <p className="text-sm text-muted-foreground">{r.description}</p>}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
