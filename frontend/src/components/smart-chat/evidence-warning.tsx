import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Upload, FileText, ArrowRight } from 'lucide-react';

export interface EvidenceGap {
  /** 缺少的证据类型 */
  type: string;
  /** 具体缺少什么 */
  description: string;
  /** 为什么重要 */
  importance: string;
  /** 建议的补充方式 */
  suggestion?: string;
}

interface EvidenceWarningProps {
  gaps: EvidenceGap[];
  onUploadEvidence?: () => void;
  onViewEvidencePage?: () => void;
}

export function EvidenceWarning({ gaps, onUploadEvidence, onViewEvidencePage }: EvidenceWarningProps) {
  if (!gaps || gaps.length === 0) {
    return null;
  }

  return (
    <Alert variant="destructive" className="mt-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle className="flex items-center justify-between">
        <span>证据缺失提醒</span>
        <span className="text-xs font-normal">缺少 {gaps.length} 项关键证据</span>
      </AlertTitle>
      <AlertDescription className="space-y-3 mt-2">
        <div className="space-y-2">
          {gaps.map((gap, i) => (
            <div key={i} className="bg-destructive/10 rounded p-2 text-sm">
              <div className="flex items-start gap-2">
                <span className="font-medium text-destructive min-w-fit">{gap.type}</span>
                <div className="flex-1">
                  <p className="text-foreground">{gap.description}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    <span className="text-destructive/80">重要性：</span>{gap.importance}
                  </p>
                  {gap.suggestion && (
                    <p className="text-xs text-muted-foreground mt-1">
                      <span className="text-green-600 dark:text-green-400">建议：</span>{gap.suggestion}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {(onUploadEvidence || onViewEvidencePage) && (
          <div className="flex gap-2 pt-2 border-t border-destructive/20">
            {onUploadEvidence && (
              <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onUploadEvidence}>
                <Upload className="h-3 w-3 mr-1" />
                上传证据
              </Button>
            )}
            {onViewEvidencePage && (
              <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={onViewEvidencePage}>
                <FileText className="h-3 w-3 mr-1" />
                查看证据管理
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            )}
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}

export default EvidenceWarning;
