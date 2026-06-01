import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, ArrowRight, Sparkles } from 'lucide-react';

export interface RecommendedDocument {
  type: string;
  reason: string;
  priority: string;
}

interface DocumentRecommendationsProps {
  documents: RecommendedDocument[];
  onGenerateDoc: (docType: string) => void;
  onGenerateAllDocs?: (docs: RecommendedDocument[]) => void;
  isGenerating?: boolean;
}

export function DocumentRecommendations({
  documents,
  onGenerateDoc,
  onGenerateAllDocs,
  isGenerating = false,
}: DocumentRecommendationsProps) {
  if (!documents || documents.length === 0) {
    return null;
  }

  return (
    <Card className="mt-3 mb-3 border-primary/20 bg-gradient-to-br from-primary/5 to-background">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <p className="text-sm font-medium">推荐文书草稿（点击起草）</p>
          </div>
          {documents.length > 1 && onGenerateAllDocs && (
            <Button
              variant="default"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onGenerateAllDocs(documents)}
              disabled={isGenerating}
            >
              <Sparkles className="mr-1 h-3 w-3" />
              {isGenerating ? '起草中...' : '批量起草草稿'}
            </Button>
          )}
        </div>

        {/* 文书链接列表 */}
        <div className="space-y-2">
          {documents.map((doc, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg border bg-background p-3 hover:bg-muted/50 transition-colors cursor-pointer group"
              onClick={() => onGenerateDoc(doc.type)}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="rounded bg-primary/10 p-1.5">
                  <FileText className="h-4 w-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm group-hover:text-primary transition-colors">
                      {doc.type}
                    </span>
                    {doc.priority === 'high' && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 text-red-700">重要</span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{doc.reason}</p>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 ml-2" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default DocumentRecommendations;
