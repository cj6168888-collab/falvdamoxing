import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { resolveGap } from '@/api/profile.api';
import { useState } from 'react';
import type { EvidenceGap } from '@/types/profile.types';

interface Props {
  caseId: string;
  gapsData?: EvidenceGap;
}

export function EvidenceGapsList({ caseId, gapsData }: Props) {
  const [resolving, setResolving] = useState<string | null>(null);
  const gaps = gapsData?.unresolved_gaps || [];

  const handleResolve = async (gapId: string) => {
    setResolving(gapId);
    try {
      await resolveGap(Number(caseId), gapId, '用户确认已补充');
    } catch (e) {
      console.error('Failed to resolve gap:', e);
    } finally {
      setResolving(null);
    }
  };

  const severityConfig = {
    high: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-950/20', border: 'border-red-200 dark:border-red-800' },
    medium: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-950/20', border: 'border-yellow-200 dark:border-yellow-800' },
    low: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-950/20', border: 'border-green-200 dark:border-green-800' },
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>证据缺口</span>
          {gaps.length > 0 && (
            <Badge variant="destructive">{gaps.length} 个未解决</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {gaps.length === 0 ? (
          <div className="py-8 text-center">
            <CheckCircle className="mx-auto mb-2 h-8 w-8 text-green-500" />
            <p className="text-sm text-muted-foreground">暂无未解决的证据缺口</p>
          </div>
        ) : (
          <div className="space-y-3">
            {gaps.map((gap) => {
              const config = severityConfig[gap.severity as keyof typeof severityConfig] || severityConfig.medium;
              const Icon = config.icon;
              return (
                <div
                  key={gap.id}
                  className={`flex items-center justify-between rounded-lg border p-3 ${config.bg} ${config.border}`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-5 w-5 ${config.color}`} />
                    <div>
                      <p className="text-sm font-medium">{gap.type}</p>
                      <p className="text-xs text-muted-foreground">状态: {gap.status}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={resolving === gap.id}
                    onClick={() => handleResolve(gap.id)}
                  >
                    {resolving === gap.id ? '处理中...' : '标记已解决'}
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
