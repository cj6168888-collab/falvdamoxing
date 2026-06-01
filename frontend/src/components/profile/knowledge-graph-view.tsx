import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { KnowledgeGraphData } from '@/types/profile.types';
import { knowledgeTypeLabels } from '@/types/profile.types';

interface Props {
  graphData: KnowledgeGraphData;
}

export function KnowledgeGraphView({ graphData }: Props) {
  const { nodes, edges, stats } = graphData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>知识图谱</span>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{stats.total_nodes} 节点</Badge>
            <Badge variant="outline">{stats.total_edges} 关系</Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.by_type).map(([type, count]) => (
              <Badge key={type} variant="outline" className="gap-1">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ backgroundColor: type === 'fact' ? '#3b82f6' : type === 'evidence' ? '#22c55e' : type === 'claim' ? '#f59e0b' : type === 'legal' ? '#8b5cf6' : '#ec4899' }}
                />
                {knowledgeTypeLabels[type] || type}: {count}
              </Badge>
            ))}
          </div>

          <div className="h-[400px] overflow-auto rounded-lg border bg-muted/20">
            <div className="p-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {nodes.map((node) => (
                  <div
                    key={node.id}
                    className="rounded-lg border p-3"
                    style={{ borderLeftColor: node.color, borderLeftWidth: '3px' }}
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-xs font-medium" style={{ color: node.color }}>
                        {knowledgeTypeLabels[node.type] || node.type}
                      </span>
                      {node.verified && (
                        <Badge variant="success" className="text-xs">已验证</Badge>
                      )}
                    </div>
                    <p className="text-sm">{node.label}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      识别参考: {(node.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {edges.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-medium">关系列表</p>
              <div className="max-h-[200px] space-y-1 overflow-auto rounded border p-2 text-xs">
                {edges.map((edge, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="font-mono">{edge.source}</span>
                    <span className="text-muted-foreground">
                      {edge.type === 'related' ? '→ 关联 →' : edge.type === 'contradicts' ? '→ 矛盾 →' : '→'}
                    </span>
                    <span className="font-mono">{edge.target}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
