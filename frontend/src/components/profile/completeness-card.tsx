import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import type { ProfileSummary } from '@/types/profile.types';
import { completenessLevelMap, knowledgeTypeLabels } from '@/types/profile.types';

interface Props {
  profile: ProfileSummary;
}

export function CompletenessCard({ profile }: Props) {
  const { summary } = profile;
  const score = summary.completeness.score;
  const level = summary.completeness.level;
  const levelInfo = completenessLevelMap[level] || completenessLevelMap['稀疏'];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>案件画像概览</span>
          <Badge variant={score >= 60 ? 'default' : score >= 30 ? 'secondary' : 'destructive'}>
            {levelInfo.label}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">完整度评分</span>
            <span className="font-medium">{score.toFixed(1)} / 100</span>
          </div>
          <Progress value={score} className="h-2" />
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatItem label="知识原子" value={summary.knowledge_stats.total.toString()} />
          <StatItem label="对话轮次" value={summary.conversation_count.toString()} />
          <StatItem label="证据数量" value={summary.evidence_count.toString()} />
          <StatItem label="未解决缺口" value={summary.unresolved_gaps.length.toString()} />
        </div>

        {summary.knowledge_stats.total > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">知识分布</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(summary.knowledge_stats.by_type).map(([type, count]) => (
                <Badge key={type} variant="outline" className="gap-1">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ backgroundColor: type === 'fact' ? '#3b82f6' : type === 'evidence' ? '#22c55e' : type === 'claim' ? '#f59e0b' : type === 'legal' ? '#8b5cf6' : '#ec4899' }}
                  />
                  {knowledgeTypeLabels[type] || type}: {count}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {summary.last_updated && (
          <p className="text-xs text-muted-foreground">
            最后更新: {new Date(summary.last_updated).toLocaleString('zh-CN')}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-3 text-center">
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
