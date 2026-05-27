import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Landmark, Briefcase, Plus, TrendingUp, AlertCircle, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface ExecutionOverview {
  execution_amount?: number;
  executed_amount?: number;
}

interface ExecutionAsset {
  id: string | number;
  asset_name?: string;
  asset_type?: string;
  estimated_value?: number;
  status?: string;
  progress?: number;
  control_method?: string;
}

interface ExecutionSuggestion {
  suggested_asset_name?: string;
  reason?: string;
}

export default function CaseExecutionPage() {
  const { id } = useParams<{ id: string }>();

  const { data: executionAssets, isLoading } = useQuery({
    queryKey: ['case-execution', id],
    queryFn: () => axiosInstance.get<ExecutionAsset[]>(`/api/execution/case/${id}/assets`).then(res => res.data).catch(() => []),
    enabled: !!id,
  });

  const { data: overview } = useQuery({
    queryKey: ['case-execution-overview', id],
    queryFn: () => axiosInstance.get<ExecutionOverview>(`/api/execution/case/${id}/overview`).then(res => res.data).catch((): ExecutionOverview => ({})),
    enabled: !!id,
  });

  const { data: suggestions } = useQuery({
    queryKey: ['case-execution-suggestions', id],
    queryFn: () => axiosInstance.get<ExecutionSuggestion[]>(`/api/execution/case/${id}/discover-assets`).then(res => res.data).catch(() => []),
    enabled: !!id,
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2"><Landmark className="h-5 w-5 text-primary" />判决执行与财产线索追踪</h2>
          <p className="text-sm text-muted-foreground mt-1">管理强制执行阶段的财产线索、查封冻结状态及回款进度</p>
        </div>
        <div className="flex gap-2">
          {suggestions && suggestions.length > 0 && (
            <Badge variant="secondary" className="bg-orange-100 text-orange-700 animate-pulse border-orange-200">
              发现 {suggestions.length} 条证据线索
            </Badge>
          )}
          <Button><Plus className="h-4 w-4 mr-2" />新增财产线索</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">执行目标总额</p>
              <h3 className="text-2xl font-bold mt-1">￥{overview?.execution_amount?.toLocaleString() || '待定'}</h3>
            </div>
            <TrendingUp className="h-8 w-8 text-primary opacity-50" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">已发现财产估值</p>
              <h3 className="text-2xl font-bold mt-1">￥{(executionAssets?.reduce((acc, cur) => acc + (cur.estimated_value || 0), 0) || 0).toLocaleString()}</h3>
            </div>
            <Briefcase className="h-8 w-8 text-muted-foreground opacity-50" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">实际执行到位金额</p>
              <h3 className="text-2xl font-bold mt-1 text-green-600">￥{overview?.executed_amount?.toLocaleString() || '0.00'}</h3>
            </div>
            <Landmark className="h-8 w-8 text-green-600 opacity-50" />
          </CardContent>
        </Card>
      </div>

      {/* AI Discovery Section */}
      {suggestions && suggestions.length > 0 && (
        <Card className="border-orange-200 bg-orange-50/30 overflow-hidden">
          <CardHeader className="bg-orange-50/50 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1 px-2 bg-orange-500 text-white rounded text-[10px] font-bold">AI DISCOVERY</div>
              <CardTitle className="text-sm font-bold text-orange-800">从案件证据中自动发现的财产线索</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {suggestions.map((suggestion, idx) => (
                <div key={idx} className="bg-white p-3 rounded-md border border-orange-100 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-sm font-bold text-orange-900">{suggestion.suggested_asset_name}</span>
                      <FileText className="h-4 w-4 text-orange-400" />
                    </div>
                    <p className="text-xs text-orange-700/80 mb-2 line-clamp-2">{suggestion.reason}</p>
                  </div>
                  <Button size="sm" variant="outline" className="h-7 text-xs border-orange-200 text-orange-700 hover:bg-orange-50 mt-1">
                    引入为执行线索
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {(!executionAssets || executionAssets.length === 0) ? (
        <Card className="border-dashed">
          <CardContent className="h-64 flex flex-col items-center justify-center text-center">
            <AlertCircle className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <h3 className="text-lg font-medium mb-1">暂无财产线索</h3>
            <p className="text-muted-foreground text-sm">如案件已进入强制执行阶段，可录入房产、车辆、账户等线索以跟踪法院查封/拍卖进度。</p>
            <Button variant="outline" className="mt-6"><Plus className="h-4 w-4 mr-2" />录入首条线索</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {executionAssets.map((asset) => (
            <Card key={asset.id} className="hover:border-primary/50 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-base">{asset.asset_name}</CardTitle>
                  <Badge variant="outline">{asset.status || '发现'}</Badge>
                </div>
                <CardDescription>{asset.asset_type || '类型未知'}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>查控进度</span>
                      <span>{asset.progress || 0}%</span>
                    </div>
                    <Progress value={asset.progress || 0} className="h-2" />
                  </div>
                  <div className="text-sm grid grid-cols-2 gap-2 text-muted-foreground">
                    <div>估值: <span className="text-foreground font-medium">{asset.estimated_value || '待定'}</span></div>
                    <div>控制方式: <span className="text-foreground font-medium">{asset.control_method || '未控制'}</span></div>
                  </div>
                </div>
                <Button variant="ghost" size="sm" className="w-full mt-4 border border-dashed"><FileText className="h-3 w-3 mr-2"/>上传法律文书 (裁定/协助通知书)</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
