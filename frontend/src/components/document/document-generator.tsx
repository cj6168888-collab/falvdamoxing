import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useGenerateDocument, useDocumentTemplates } from '@/hooks/use-document';
import { toast } from 'sonner';
import { Sparkles, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { useCaseDetail } from '@/hooks/use-case';

interface Props {
  caseId: string;
  onClose?: () => void;
  onGenerated?: (doc: unknown) => void;
}

function getErrorMessage(error: unknown): string {
  const response = (error as { response?: { data?: { detail?: string } } }).response;
  return response?.data?.detail || '文书生成失败';
}

export function DocumentGenerator({ caseId, onClose, onGenerated }: Props) {
  const [docType, setDocType] = useState('起诉状');
  const [customReq, setCustomReq] = useState('');
  const [evidenceStrategy, setEvidenceStrategy] = useState('');
  const [claimStrategy, setClaimStrategy] = useState('');
  const [emphasis, setEmphasis] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Automatically fetch case details to display some context
  const { data: caseData } = useCaseDetail(caseId);
  const { data: templates } = useDocumentTemplates();
  const generate = useGenerateDocument();

  // Basic auto-fill context string
  const contextPreview = caseData 
    ? `原告：${caseData.plaintiff?.name || '未知'}\n被告：${caseData.defendant?.name || '未知'}\n纠纷类型：${caseData.type}`
    : '加载案件信息中...';

  const handleGenerate = () => {
    if (!docType) {
      toast.error('请选择文书类型');
      return;
    }
    const toastId = toast.loading(`正在由 AI 起草综合关联了案情事实的《${docType}》...`);
    generate.mutate({ 
      caseId, 
      data: { 
        document_type: docType, 
        custom_requirements: customReq,
        evidence_strategy: evidenceStrategy,
        claim_strategy: claimStrategy,
        emphasis: emphasis
      } 
    }, {
      onSuccess: (doc) => {
        toast.success(`《${docType}》生成成功！可前往列表查看或修改`, { id: toastId });
        setCustomReq('');
        setEvidenceStrategy('');
        setClaimStrategy('');
        setEmphasis('');
        onGenerated?.(doc);
        onClose?.();
      },
      onError: (e: unknown) => {
        toast.error(getErrorMessage(e), { id: toastId });
      }
    });
  };

  return (
    <Card className="border-primary/20 shadow-sm">
      <CardHeader className="bg-primary/5 pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          智能法律文书生成
        </CardTitle>
        <CardDescription>
          系统会自动带入您已填写的案件信息（原被告、诉求、前期 AI 分析的事实等）。您只需补充以下撰写策略。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5 pt-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>文书分类 <span className="text-destructive">*</span></Label>
            <Select value={docType} onValueChange={setDocType}>
              <SelectTrigger>
                <SelectValue placeholder="选择生成的文书..." />
              </SelectTrigger>
              <SelectContent>
                {templates?.map((t) => (
                  <SelectItem key={t.type || t.name} value={t.type || t.name}>{t.name}</SelectItem>
                )) || (
                  <>
                    <SelectItem value="起诉状">起诉状</SelectItem>
                    <SelectItem value="答辩状">答辩状</SelectItem>
                    <SelectItem value="律师函">律师函</SelectItem>
                    <SelectItem value="代理词">代理词</SelectItem>
                    <SelectItem value="管辖权异议申请书">管辖权异议申请书</SelectItem>
                  </>
                )}
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label className="text-muted-foreground flex items-center gap-1">已获取系统前置案情 <FileText className="h-3 w-3"/></Label>
            <div className="text-xs text-muted-foreground bg-muted p-2 h-10 flex items-center rounded border whitespace-pre truncate">
              {contextPreview}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label>核心诉求或补充定制要求</Label>
          <Textarea 
            value={customReq} 
            onChange={(e) => setCustomReq(e.target.value)} 
            placeholder="例如：本案原告仅追讨本金，放弃违约金诉求；要求加上要求被告承担全部诉讼费的条款。" 
            rows={3} 
          />
        </div>

        <div>
          <Button 
            variant="ghost" 
            size="sm" 
            className="p-0 h-auto text-xs text-muted-foreground flex items-center"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? <ChevronUp className="h-3 w-3 mr-1"/> : <ChevronDown className="h-3 w-3 mr-1"/>}
            高级撰写策略 (适用复杂庭审)
          </Button>
          
          {showAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 p-4 bg-muted/30 border rounded-lg border-dashed">
              <div className="space-y-2">
                <Label className="text-xs">证据策略 (Evidence Strategy)</Label>
                <Input 
                  value={evidenceStrategy} 
                  onChange={(e) => setEvidenceStrategy(e.target.value)}
                  placeholder="例：避开提到合同第三方的责任，仅强调被告" 
                  className="h-8 text-xs bg-white"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">主张策略 (Claim Strategy)</Label>
                <Input 
                  value={claimStrategy} 
                  onChange={(e) => setClaimStrategy(e.target.value)}
                  placeholder="例：主攻表见代理，次攻债务加入" 
                  className="h-8 text-xs bg-white"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label className="text-xs">行文重点强调 (Emphasis)</Label>
                <Input 
                  value={emphasis} 
                  onChange={(e) => setEmphasis(e.target.value)}
                  placeholder="例：使用更严厉的措辞，突出对方违约带来的恶劣商业影响" 
                  className="h-8 text-xs bg-white"
                />
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end pt-2 border-t">
          <Button onClick={handleGenerate} disabled={generate.isPending} className="w-full sm:w-auto">
            {generate.isPending ? <><Sparkles className="mr-2 h-4 w-4 animate-spin" />正在深度创作文书...</> : <><FileText className="mr-2 h-4 w-4" />一键生成 {docType}</>}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
