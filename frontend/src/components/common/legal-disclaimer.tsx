import { AlertTriangle } from 'lucide-react';

type LegalDisclaimerVariant = 'analysis' | 'document' | 'evidence' | 'adversarial' | 'general';

interface LegalDisclaimerProps {
  variant?: LegalDisclaimerVariant;
  compact?: boolean;
}

const DISCLAIMER_TEXT: Record<LegalDisclaimerVariant, string> = {
  analysis:
    '以下内容由 AI 根据当前材料生成，仅供案件事实整理和风险识别参考。请结合完整证据、现行法律法规和专业人士意见进行核验。',
  document:
    '生成结果为文书草稿，不等同于正式法律文书。提交、发送或对外使用前，请逐项核验当事人信息、事实依据、诉讼请求、证据目录、法条引用、金额计算和签名盖章事项。',
  evidence:
    '证据分析仅为证明力和风险参考，不能替代法院对证据真实性、合法性、关联性的最终认定。',
  adversarial:
    '对抗分析用于模拟可能争议焦点和抗辩路径，不构成诉讼结果预测或胜诉承诺。',
  general:
    '本系统生成内容为法律工作辅助材料，仅供事实整理、证据分析、风险提示和文书草稿参考，所有对外使用均需人工核验确认。',
};

export function LegalDisclaimer({ variant = 'general', compact = false }: LegalDisclaimerProps) {
  return (
    <div className={`rounded-md border border-amber-200 bg-amber-50 text-amber-900 ${compact ? 'px-3 py-2' : 'p-3'}`}>
      <div className="flex gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        <p className={compact ? 'text-xs leading-5' : 'text-sm leading-6'}>{DISCLAIMER_TEXT[variant]}</p>
      </div>
    </div>
  );
}

export default LegalDisclaimer;
