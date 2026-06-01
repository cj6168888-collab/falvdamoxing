import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight, FileText, Star, AlertCircle } from 'lucide-react';

export interface EvidenceUnderstanding {
  id: number;
  displayName: string;
  type: string;
  summary?: string;
  keyPoints?: string[];
  credibility?: string;
  relevance?: string; // 与当前问题的相关性
}

interface EvidenceSummaryProps {
  evidenceList: EvidenceUnderstanding[];
  maxDisplay?: number;
  showAll?: boolean;
  onShowAllChange?: (show: boolean) => void;
}

export function EvidenceSummary({
  evidenceList,
  maxDisplay = 5,
  showAll = false,
  onShowAllChange,
}: EvidenceSummaryProps) {
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  if (!evidenceList || evidenceList.length === 0) {
    return null;
  }

  const toggleExpand = (id: number) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const displayedList = showAll ? evidenceList : evidenceList.slice(0, maxDisplay);

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      contract: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      invoice: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      correspondence: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      communication: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      identification: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
      witness: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      appraisal: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      video_audio: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
      other: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
    };
    return colors[type] || colors.other;
  };

  return (
    <Card className="bg-slate-50 dark:bg-slate-950/20">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="h-4 w-4" />
          AI 已读取的证据
          <Badge variant="outline" className="ml-auto">{evidenceList.length} 份</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {displayedList.map((ev) => (
          <Collapsible
            key={ev.id}
            open={expandedItems.has(ev.id)}
            onOpenChange={() => toggleExpand(ev.id)}
          >
            <div className="border rounded-lg p-2">
              <div className="flex items-start gap-2">
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 flex-shrink-0">
                    {expandedItems.has(ev.id) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                </CollapsibleTrigger>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{ev.displayName}</span>
                    <Badge className={`text-xs ${getTypeColor(ev.type)}`}>
                      {ev.type}
                    </Badge>
                  </div>
                  {ev.summary && !expandedItems.has(ev.id) && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                      {ev.summary}
                    </p>
                  )}
                </div>
              </div>

              <CollapsibleContent>
                <div className="mt-2 pt-2 border-t space-y-2">
                  {ev.summary && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">证据摘要</p>
                      <p className="text-xs mt-0.5">{ev.summary}</p>
                    </div>
                  )}
                  {ev.keyPoints && ev.keyPoints.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">关键内容</p>
                      <ul className="list-disc pl-4 mt-0.5 space-y-0.5">
                        {ev.keyPoints.map((point, i) => (
                          <li key={i} className="text-xs">{point}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {ev.credibility && (
                    <div className="flex items-center gap-1">
                      <Star className="h-3 w-3 text-amber-500" />
                      <span className="text-xs">证明力参考：{ev.credibility}</span>
                    </div>
                  )}
                  {ev.relevance && (
                    <div className="flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 text-blue-500" />
                      <span className="text-xs">相关性：{ev.relevance}</span>
                    </div>
                  )}
                </div>
              </CollapsibleContent>
            </div>
          </Collapsible>
        ))}

        {evidenceList.length > maxDisplay && onShowAllChange && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full h-7 text-xs"
            onClick={() => onShowAllChange(!showAll)}
          >
            {showAll ? '收起' : `还有 ${evidenceList.length - maxDisplay} 份证据`}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default EvidenceSummary;
