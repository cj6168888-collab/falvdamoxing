import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const REVIEW_ITEMS = [
  { id: 'parties', label: '当事人名称、身份证号或统一社会信用代码已核对' },
  { id: 'court_jurisdiction', label: '法院、管辖依据和案由已核对' },
  { id: 'claims_amounts', label: '诉讼请求、金额、利息和计算方式已核对' },
  { id: 'facts_evidence', label: '事实与理由均已对应证据或列入待补证事项' },
  { id: 'law_validity', label: '法条、案例、案号和现行有效性已另行核验' },
  { id: 'evidence_catalog', label: '证据目录、证据编号和证明目的已核对' },
  { id: 'dates_signature', label: '日期、签名、盖章和提交版本已确认' },
  { id: 'authorization_consequences', label: '授权材料和对外发送后果已向委托人确认' },
] as const;

interface Props {
  open: boolean;
  documentTitle?: string;
  exportLabel?: string;
  isLoading?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (checkedItems: string[]) => void;
}

export function DocumentExportReviewDialog({
  open,
  documentTitle,
  exportLabel = '导出文书',
  isLoading = false,
  onOpenChange,
  onConfirm,
}: Props) {
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!open) {
      setCheckedIds(new Set());
    }
  }, [open]);

  const allChecked = checkedIds.size === REVIEW_ITEMS.length;
  const checkedCount = checkedIds.size;
  const title = documentTitle || '当前文书草稿';

  const progressText = useMemo(
    () => `${checkedCount}/${REVIEW_ITEMS.length} 项已核验`,
    [checkedCount],
  );

  const toggleItem = (id: string, checked: boolean) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-primary" />
            文书导出前核验清单
          </DialogTitle>
          <DialogDescription>
            《{title}》仍属于法律工作底稿。请完成以下核验后再{exportLabel}。
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>
              系统生成内容不能直接视为正式法律文书。对外提交、发送或归档前，应由使用者结合完整材料逐项确认。
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {REVIEW_ITEMS.map((item) => (
            <label
              key={item.id}
              className="flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm hover:bg-muted/50"
            >
              <Checkbox
                checked={checkedIds.has(item.id)}
                onCheckedChange={(checked) => toggleItem(item.id, checked === true)}
                aria-label={item.label}
              />
              <span className="leading-5">{item.label}</span>
            </label>
          ))}
        </div>

        <DialogFooter className="items-center gap-2 sm:justify-between">
          <span className="text-sm text-muted-foreground">{progressText}</span>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
              取消
            </Button>
            <Button onClick={() => onConfirm([...checkedIds])} disabled={!allChecked || isLoading}>
              {isLoading ? '处理中...' : exportLabel}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
