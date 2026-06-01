import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

interface Props { caseId: string; onGenerate: (type: string) => void; }

export function AppealDocGenerator({ caseId: _caseId, onGenerate }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>上诉文书草稿</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full" onClick={() => onGenerate('上诉状')}>
          <FileText className="mr-2 h-4 w-4" />起草上诉状草稿
        </Button>
        <Button className="w-full" variant="outline" onClick={() => onGenerate('答辩意见')}>
          <FileText className="mr-2 h-4 w-4" />起草答辩意见草稿
        </Button>
        <Button className="w-full" variant="outline" onClick={() => onGenerate('新证据清单')}>
          <FileText className="mr-2 h-4 w-4" />整理新证据清单草稿
        </Button>
      </CardContent>
    </Card>
  );
}
