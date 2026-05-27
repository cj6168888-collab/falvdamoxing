import { useParams } from 'react-router-dom';
import { useCaseProfile } from '@/hooks/use-profile';
import { useKnowledgeGraph, useEvidenceGaps, useBuildProfile } from '@/api/profile.api';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { CompletenessCard } from '@/components/profile/completeness-card';
import { KnowledgeBaseList } from '@/components/profile/knowledge-base-list';
import { EvidenceGapsList } from '@/components/profile/evidence-gaps-list';
import { ConversationTimeline } from '@/components/profile/conversation-timeline';
import { KnowledgeGraphView } from '@/components/profile/knowledge-graph-view';
import { ProfileTips } from '@/components/profile/profile-tips';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

export default function CaseProfilePage() {
  const { id } = useParams<{ id: string }>();
  const caseId = id || '';
  const { profile, isLoading: profileLoading } = useCaseProfile(caseId);
  const { data: graphData, isLoading: graphLoading } = useKnowledgeGraph(caseId);
  const { data: gapsData, isLoading: gapsLoading } = useEvidenceGaps(caseId);
  const { build, isBuilding, result } = useBuildProfile(caseId);

  if (profileLoading || graphLoading || gapsLoading) {
    return <PageSkeleton />;
  }

  if (!profile) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 text-center">
        <p className="text-lg text-muted-foreground">暂无案件画像数据</p>
        <Button className="mt-4" onClick={() => build()} disabled={isBuilding}>
          {isBuilding ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          生成案件画像
        </Button>
      </div>
    );
  }

  const hasData = (profile.summary?.knowledge_stats?.total ?? 0) > 0 || (profile.summary?.conversation_count ?? 0) > 0 || (profile.summary?.evidence_count ?? 0) > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">案件画像分析</h2>
        <Button variant="outline" size="sm" onClick={() => build()} disabled={isBuilding}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isBuilding ? 'animate-spin' : ''}`} />
          {isBuilding ? 'AI分析中...' : result ? '重新分析' : 'AI增强分析'}
        </Button>
      </div>

      {!hasData && (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">案件数据较少，画像分析结果有限</p>
          <p className="mt-1 text-sm text-muted-foreground">建议先添加案件描述、上传证据或进行对话</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <CompletenessCard profile={profile} />
        </div>
        <div>
          <ProfileTips tips={profile.profile_tips || []} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <EvidenceGapsList caseId={caseId} gapsData={gapsData} />
        <KnowledgeBaseList knowledge={profile.recent_knowledge || []} />
      </div>

      <ConversationTimeline conversations={profile.recent_conversations || []} />

      {graphData && graphData.nodes.length > 0 && (
        <KnowledgeGraphView graphData={graphData} />
      )}
    </div>
  );
}
