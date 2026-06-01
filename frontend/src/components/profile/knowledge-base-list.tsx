import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { BookOpen } from 'lucide-react';
import type { ProfileSummary } from '@/types/profile.types';
import { knowledgeTypeLabels, knowledgeTypeColors } from '@/types/profile.types';

interface Props {
  knowledge: ProfileSummary['recent_knowledge'];
}

export function KnowledgeBaseList({ knowledge }: Props) {
  if (!knowledge || knowledge.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>知识库</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center">
            <BookOpen className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">暂无知识数据</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>知识库</span>
          <Badge variant="secondary">{knowledge.length} 条</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[320px] pr-4">
          <div className="space-y-3">
            {knowledge.map((atom) => (
              <div key={atom.atom_id} className="rounded-lg border p-3">
                <div className="mb-2 flex items-center justify-between">
                  <Badge
                    variant="outline"
                    className="gap-1"
                    style={{ borderColor: knowledgeTypeColors[atom.type] || '#94a3b8' }}
                  >
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{ backgroundColor: knowledgeTypeColors[atom.type] || '#94a3b8' }}
                    />
                    {knowledgeTypeLabels[atom.type] || atom.type}
                  </Badge>
                  <div className="flex items-center gap-2">
                    {atom.verified && (
                      <Badge variant="success" className="text-xs">已验证</Badge>
                    )}
                    <span className="text-xs text-muted-foreground">
                      识别参考: {(atom.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <p className="text-sm">{atom.content}</p>
                {atom.keywords.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {atom.keywords.slice(0, 5).map((kw) => (
                      <span key={kw} className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
