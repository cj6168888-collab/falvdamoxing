import { DataStat } from '@/components/common/data-stat';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCaseDetail } from '@/hooks/use-case';
import { useEvidenceCount } from '@/api/evidence.api';
import { useParams } from 'react-router-dom';

interface CasePanorama {
  execution_intelligence?: {
    assets_discovered?: Array<{ name: string; value: string | number }>;
  };
  financial_summary?: {
    win_rate_estimate?: string | number;
  };
}

export default function CaseOverviewPage() {
  const { id } = useParams<{ id: string }>();
  const { data } = useCaseDetail(id || '');
  const { data: evidenceCount } = useEvidenceCount(id || '');
  const panorama = (data as typeof data & { panorama?: CasePanorama })?.panorama;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DataStat label="诉讼金额" value={data?.amount || 0} />
        <DataStat label="证据项" value={data?.evidenceCount || evidenceCount || 0} />
        <DataStat label="财产线索" value={panorama?.execution_intelligence?.assets_discovered?.length || 0} />
        <DataStat label="庭审记录" value={0} />
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>案件基础信息</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div><p className="text-sm text-muted-foreground">案件类型</p><p>{data?.type}</p></div>
              <div><p className="text-sm text-muted-foreground">当前状态</p><p className="font-medium text-blue-600">{data?.status}</p></div>
              <div><p className="text-sm text-muted-foreground">原告/申请人</p><p>{data?.plaintiff?.name || '未记录'}</p></div>
              <div><p className="text-sm text-muted-foreground">被告/被执行人</p><p>{data?.defendant?.name || '未记录'}</p></div>
            </div>
            {data?.description && (
              <div>
                <p className="text-sm text-muted-foreground">案件描述</p>
                <p className="text-sm leading-relaxed">{data.description}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>AI 全景情报摘要</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {panorama ? (
              <>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">最新财产线索</p>
                  <div className="mt-2 space-y-2">
                    {panorama.execution_intelligence?.assets_discovered?.slice(0, 2).map((a, i) => (
                      <div key={i} className="rounded bg-muted p-2 text-xs">
                        <span className="font-bold">{a.name}</span>: 估值 {a.value}
                      </div>
                    )) || <p className="text-xs italic text-muted-foreground">暂无发现</p>}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">裁判支持度参考</p>
                  <p className="mt-1 text-2xl font-bold text-green-600">
                    {panorama.financial_summary?.win_rate_estimate || '待评估'}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">仅作风险工作底稿参考，需结合证据和律师复核。</p>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground italic">情报整理中...</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
