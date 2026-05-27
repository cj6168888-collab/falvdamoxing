import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCaseProfile } from '@/hooks/use-profile';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { completenessLevelMap, knowledgeTypeLabels, knowledgeTypeColors } from '@/types/profile.types';

interface Props { caseId: string; }

type LegacyProfile = {
  coreDispute?: string;
  winProbability?: number;
  riskLevel?: string;
  keyEvidence?: string[];
  evidenceGaps?: unknown[];
};

function getSummary(profile: unknown) {
  const current = profile as {
    summary?: {
      completeness?: { score?: number; level?: string };
      knowledge_stats?: { total?: number; by_type?: Record<string, number> };
      conversation_count?: number;
      evidence_count?: number;
      unresolved_gaps?: unknown[];
    };
  };
  const legacy = profile as LegacyProfile;

  if (current.summary && typeof current.summary === 'object') {
    return {
      score: current.summary.completeness?.score ?? legacy.winProbability ?? 0,
      level: current.summary.completeness?.level ?? legacy.riskLevel ?? '\u7a00\u758f',
      knowledgeTotal: current.summary.knowledge_stats?.total ?? legacy.keyEvidence?.length ?? 0,
      knowledgeByType: current.summary.knowledge_stats?.by_type ?? {},
      conversationCount: current.summary.conversation_count ?? 0,
      evidenceCount: current.summary.evidence_count ?? legacy.keyEvidence?.length ?? 0,
      unresolvedCount: current.summary.unresolved_gaps?.length ?? legacy.evidenceGaps?.length ?? 0,
    };
  }

  return {
    score: legacy.winProbability ?? 0,
    level: legacy.riskLevel ?? '\u7a00\u758f',
    knowledgeTotal: legacy.keyEvidence?.length ?? 0,
    knowledgeByType: {},
    conversationCount: 0,
    evidenceCount: legacy.keyEvidence?.length ?? 0,
    unresolvedCount: legacy.evidenceGaps?.length ?? 0,
  };
}

export function ProfileSummary({ caseId }: Props) {
  const { profile, isLoading } = useCaseProfile(caseId);

  if (isLoading) return <PageSkeleton />;

  if (!profile) {
    return (
      <Card>
        <CardHeader><CardTitle>{'\u6848\u4ef6\u753b\u50cf'}</CardTitle></CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{'\u6682\u65e0\u753b\u50cf\u6570\u636e'}</p>
        </CardContent>
      </Card>
    );
  }

  const summary = getSummary(profile);
  const legacy = profile as LegacyProfile;
  const levelInfo = completenessLevelMap[summary.level] || { label: summary.level, color: '', minScore: 0 };
  const tips = (profile as { profile_tips?: string[] }).profile_tips ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>{'\u6848\u4ef6\u753b\u50cf'}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {legacy.coreDispute && (
            <p className="text-sm text-muted-foreground">{legacy.coreDispute}</p>
          )}
          {legacy.riskLevel && (
            <Badge variant="outline">{legacy.riskLevel}</Badge>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{'\u5b8c\u6574\u5ea6'}</span>
              <Badge variant={summary.score >= 60 ? 'default' : summary.score >= 30 ? 'secondary' : 'destructive'}>
                {levelInfo.label} ({summary.score.toFixed(1)})
              </Badge>
            </div>
            <Progress value={summary.score} className="h-2" />
            {legacy.winProbability !== undefined && (
              <p className="text-sm font-medium">{legacy.winProbability}%</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatItem label={'\u77e5\u8bc6\u539f\u5b50'} value={summary.knowledgeTotal.toString()} />
            <StatItem label={'\u5bf9\u8bdd\u8f6e\u6b21'} value={summary.conversationCount.toString()} />
            <StatItem label={'\u8bc1\u636e\u6570\u91cf'} value={summary.evidenceCount.toString()} />
            <StatItem label={'\u672a\u89e3\u51b3\u7f3a\u53e3'} value={summary.unresolvedCount.toString()} />
          </div>

          {summary.knowledgeTotal > 0 && Object.keys(summary.knowledgeByType).length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">{'\u77e5\u8bc6\u5206\u5e03'}</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.knowledgeByType).map(([type, count]) => (
                  <Badge key={type} variant="outline" className="gap-1">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: knowledgeTypeColors[type] || '#94a3b8' }} />
                    {knowledgeTypeLabels[type] || type}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {tips.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">{'\u667a\u80fd\u5efa\u8bae'}</p>
              {tips.map((tip, i) => (
                <p key={i} className="text-sm text-muted-foreground">- {tip}</p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
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
