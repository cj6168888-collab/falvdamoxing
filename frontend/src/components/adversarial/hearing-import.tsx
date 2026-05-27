import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

interface Props { caseId: string; onImport: () => void; }

export function HearingImport({ caseId: _caseId, onImport }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>导入到庭审</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">将对抗性分析结果导入到出庭抗辩模块</p>
        <Button onClick={onImport}>
          <FileText className="mr-2 h-4 w-4" />导入
        </Button>
      </CardContent>
    </Card>
  );
}
