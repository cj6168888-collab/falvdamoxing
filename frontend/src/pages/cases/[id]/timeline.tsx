import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Calendar, MapPin, Scale, Plus, Gavel, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import styles from './timeline.module.css';

interface TimelineNode {
  title?: string;
  node_type?: string;
  date?: string;
  location?: string;
  description?: string;
  related_evidence_ids?: Array<string | number>;
  hearing_notes?: string;
}

type BackendTimelineNode = TimelineNode & {
  event_name?: string;
  event_type?: string;
  event_date?: string;
  event_description?: string;
};

function normalizeTimelineNode(node: BackendTimelineNode): TimelineNode {
  return {
    title: node.title || node.event_name || '未命名节点',
    node_type: node.node_type || node.event_type || '节点',
    date: node.date || node.event_date,
    location: node.location,
    description: node.description || node.event_description,
    related_evidence_ids: node.related_evidence_ids,
    hearing_notes: node.hearing_notes,
  };
}

export default function CaseTimelinePage() {
  const { id } = useParams<{ id: string }>();

  // Fetch timeline / nodes
  const { data: nodes, isLoading } = useQuery({
    queryKey: ['case-timeline', id],
    queryFn: () => axiosInstance.get<BackendTimelineNode[]>(`/api/time-control/case/${id}/timeline`).then(res => res.data.map(normalizeTimelineNode)),
    enabled: !!id,
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className={`${styles.container} space-y-6`}>
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2"><Scale className="h-5 w-5 text-primary" />案件时间线与庭审记录</h2>
          <p className="text-sm text-muted-foreground mt-1">记录诉讼全周期的时间节点（立案、排期、开庭、宣判等）</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />新增节点</Button>
      </div>

      {!nodes || nodes.length === 0 ? (
        <Card className={`${styles.card} bg-muted/30 border-dashed`}>
          <CardContent className="h-64 flex flex-col items-center justify-center text-center">
            <Calendar className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">暂无时间节点记录</p>
            <Button variant="outline" className="mt-4"><Plus className="h-4 w-4 mr-2" />立即添加立案/开庭登记</Button>
          </CardContent>
        </Card>
      ) : (
        <div className={`${styles.timelineLine} relative border-l-2 border-primary/20 ml-4 space-y-8 pb-4`}>
          {nodes.map((node, idx) => (
            <div key={idx} className="relative pl-6">
              <span className="absolute -left-[9px] top-1 h-4 w-4 rounded-full bg-primary ring-4 ring-background" />
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-base">{node.title}</CardTitle>
                    <Badge variant="outline">{node.node_type || '节点'}</Badge>
                  </div>
                  <CardDescription className="flex items-center gap-4 mt-2">
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {node.date || '未定日期'}</span>
                    {node.location && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {node.location}</span>}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{node.description || '无具体描述'}</p>
                  
                  {/* Linked Evidence */}
                  {node.related_evidence_ids && node.related_evidence_ids.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {node.related_evidence_ids.map((evId) => (
                        <Badge key={evId} variant="secondary" className="px-2 py-0 h-5 text-[10px] bg-blue-50 text-blue-700 border-blue-100 flex items-center gap-1 cursor-pointer hover:bg-blue-100" onClick={() => window.location.href=`/cases/${id}/evidence?highlight=${evId}`}>
                          <FileText className="h-2 w-2" /> 证据 ID: {evId}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {/* Hearing Special Block */}
                  {node.node_type === 'hearing' && (
                    <div className="mt-4 p-3 bg-muted/50 rounded-lg border border-primary/10">
                      <h4 className="text-sm font-medium flex items-center gap-1 mb-2"><Gavel className="h-4 w-4 text-primary" />法庭调查/质证记录</h4>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap">{node.hearing_notes || '暂无庭审笔记'}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
