import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Party } from '@/types/party.types';
import { CompanyInfo } from '@/components/common/company-info';

interface Props { party: Party; onEdit: () => void; onDelete: () => void; }

export function PartyDetail({ party, onEdit, onDelete }: Props) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>{party.name}</CardTitle>
          <div className="flex gap-2">
            <button onClick={onEdit} className="text-sm text-primary hover:underline">编辑</button>
            <button onClick={onDelete} className="text-sm text-red-500 hover:underline">删除</button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div><p className="text-sm text-muted-foreground">角色</p><p>{party.role}</p></div>
        {party.phone && <div><p className="text-sm text-muted-foreground">电话</p><p>{party.phone}</p></div>}
        {party.email && <div><p className="text-sm text-muted-foreground">邮箱</p><p>{party.email}</p></div>}
        {party.address && <div><p className="text-sm text-muted-foreground">地址</p><p>{party.address}</p></div>}
        {party.agent && <div><p className="text-sm text-muted-foreground">代理人</p><p>{party.agent} {party.agentPhone ? '(' + party.agentPhone + ')' : ''}</p></div>}
        {party.companyInfo && <CompanyInfo name={party.companyInfo.name} creditCode={party.companyInfo.creditCode} legalRepresentative={party.companyInfo.legalRepresentative} status={party.companyInfo.status} />}
      </CardContent>
    </Card>
  );
}
