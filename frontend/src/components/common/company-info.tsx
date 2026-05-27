import { Building2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CompanyInfoProps {
  name: string;
  creditCode?: string;
  legalRepresentative?: string;
  status?: string;
  onVerify?: () => void;
}

export function CompanyInfo({ name, creditCode, legalRepresentative, status, onVerify }: CompanyInfoProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-4 w-4" />{name}</CardTitle>
          {status && <Badge variant={status === '正常营业' ? 'default' : 'destructive'}>{status}</Badge>}
        </div>
      </CardHeader>
      <CardContent>
        {creditCode && <p className="text-sm text-muted-foreground">信用代码: {creditCode}</p>}
        {legalRepresentative && <p className="text-sm text-muted-foreground">法定代表人: {legalRepresentative}</p>}
        {onVerify && <button onClick={onVerify} className="mt-2 text-sm text-primary hover:underline">核实信息</button>}
      </CardContent>
    </Card>
  );
}
