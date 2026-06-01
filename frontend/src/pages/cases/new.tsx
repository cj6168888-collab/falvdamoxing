import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CaseTemplateCard } from '@/components/common/case-template-card';
import { useCreateCase } from '@/hooks/use-case';
import { useAuthStore } from '@/stores/auth.store';
import type { TenantType } from '@/types/auth';
import type { Case } from '@/types/case.types';

type AudienceMode = TenantType;

interface CaseTemplate {
  type: string;
  caseType: string;
  label: string;
  fields: string[];
  evidence: string[];
  documents: string[];
}

interface AudienceCopy {
  title: string;
  templateHeading: string;
  formTitle: string;
  titleLabel: string;
  titlePlaceholder: string;
  plaintiffLabel: string;
  plaintiffPlaceholder: string;
  defendantLabel: string;
  defendantPlaceholder: string;
  amountLabel: string;
  amountPlaceholder: string;
  descriptionLabel: string;
  descriptionPlaceholder: string;
  evidenceTitle: string;
  evidenceDescription: string;
  submitLabel: string;
}

const lawFirmTemplates: CaseTemplate[] = [
  { type: 'loan', caseType: 'civil', label: '借贷纠纷', fields: ['当事人', '金额'], evidence: ['借条', '转账记录'], documents: ['律师函', '起诉状'] },
  { type: 'contract', caseType: 'civil', label: '合同纠纷', fields: ['当事人', '合同类型'], evidence: ['合同原件', '变更协议'], documents: ['解除通知', '起诉状'] },
  { type: 'tort', caseType: 'civil', label: '侵权纠纷', fields: ['当事人', '侵权行为'], evidence: ['现场照片', '医疗记录'], documents: ['起诉状', '鉴定申请'] },
  { type: 'labor', caseType: 'civil', label: '劳动争议', fields: ['员工/企业', '诉求类型'], evidence: ['劳动合同', '工资流水'], documents: ['仲裁申请'] },
];

const enterpriseTemplates: CaseTemplate[] = [
  {
    type: 'contract_review',
    caseType: 'civil',
    label: '合同审查',
    fields: ['合同相对方', '付款/验收节点'],
    evidence: ['合同文本', '补充协议', '沟通记录'],
    documents: ['风险清单', '修订建议'],
  },
  {
    type: 'debt_collection',
    caseType: 'civil',
    label: '欠款催收',
    fields: ['欠款方', '金额与账期'],
    evidence: ['合同', '对账单', '发票', '催告记录'],
    documents: ['催款函', '律师协作摘要'],
  },
  {
    type: 'labor_employment',
    caseType: 'civil',
    label: '劳动用工',
    fields: ['员工/岗位', '争议节点'],
    evidence: ['劳动合同', '工资流水', '考勤记录'],
    documents: ['处理清单', '谈话纪要'],
  },
  {
    type: 'supplier_dispute',
    caseType: 'civil',
    label: '客户供应商纠纷',
    fields: ['交易对象', '交付/质量异议'],
    evidence: ['订单合同', '验收记录', '往来函件'],
    documents: ['争议事实表', '协商提纲'],
  },
  {
    type: 'corporate_compliance',
    caseType: 'civil',
    label: '印章授权与审批',
    fields: ['事项负责人', '授权链条'],
    evidence: ['审批记录', '印章记录', '授权文件'],
    documents: ['内控检查表', '整改清单'],
  },
  {
    type: 'ip_data_risk',
    caseType: 'civil',
    label: '数据与知识产权风险',
    fields: ['业务场景', '数据/作品来源'],
    evidence: ['授权文件', '交付记录', '系统日志'],
    documents: ['风险核验表', '外部律师问题清单'],
  },
];

const personalTemplates: CaseTemplate[] = [
  {
    type: 'personal_general',
    caseType: 'civil',
    label: '先描述遇到的事',
    fields: ['发生了什么', '现在最担心什么'],
    evidence: ['聊天记录', '转账记录', '合同/票据'],
    documents: ['情况说明', '下一步清单'],
  },
  {
    type: 'urgent_risk',
    caseType: 'civil',
    label: '紧急风险判断',
    fields: ['期限/安全风险', '对方正在做什么'],
    evidence: ['通知短信', '通话录音', '现场照片'],
    documents: ['紧急处置清单', '求助清单'],
  },
  {
    type: 'personal_loan',
    caseType: 'civil',
    label: '欠款借贷',
    fields: ['借款人/出借人', '金额与还款约定'],
    evidence: ['借条', '转账记录', '催还聊天'],
    documents: ['催还提纲', '起诉材料清单'],
  },
  {
    type: 'wage_labor',
    caseType: 'civil',
    label: '劳动工资',
    fields: ['工作单位', '工资/离职情况'],
    evidence: ['劳动合同', '工资流水', '考勤记录'],
    documents: ['仲裁材料清单', '沟通提纲'],
  },
  {
    type: 'housing_rent',
    caseType: 'civil',
    label: '租房居住',
    fields: ['房东/租客', '押金或维修争议'],
    evidence: ['租赁合同', '付款记录', '房屋照片'],
    documents: ['退押沟通稿', '投诉材料'],
  },
  {
    type: 'consumer_rights',
    caseType: 'civil',
    label: '消费维权',
    fields: ['商家/平台', '商品或服务问题'],
    evidence: ['订单截图', '支付记录', '客服记录'],
    documents: ['投诉材料', '协商提纲'],
  },
  {
    type: 'family_matter',
    caseType: 'civil',
    label: '婚姻家事',
    fields: ['家庭关系', '财产/子女/沟通风险'],
    evidence: ['身份关系材料', '财产线索', '沟通记录'],
    documents: ['事实时间线', '求助清单'],
  },
  {
    type: 'traffic_injury',
    caseType: 'civil',
    label: '交通事故/人身侵权',
    fields: ['事故经过', '损害与治疗情况'],
    evidence: ['事故认定书', '病历票据', '现场照片'],
    documents: ['赔偿材料清单', '调解提纲'],
  },
];

const templatesByAudience: Record<AudienceMode, CaseTemplate[]> = {
  law_firm: lawFirmTemplates,
  enterprise: enterpriseTemplates,
  personal: personalTemplates,
};

const copyByAudience: Record<AudienceMode, AudienceCopy> = {
  law_firm: {
    title: '新建案件',
    templateHeading: '选择案件模板',
    formTitle: '案件信息',
    titleLabel: '案件标题 *',
    titlePlaceholder: '请输入案件标题',
    plaintiffLabel: '原告姓名',
    plaintiffPlaceholder: '原告姓名',
    defendantLabel: '被告姓名',
    defendantPlaceholder: '被告姓名',
    amountLabel: '诉讼金额',
    amountPlaceholder: '请输入金额',
    descriptionLabel: '案件描述',
    descriptionPlaceholder: '请描述案件情况',
    evidenceTitle: '证据材料管理',
    evidenceDescription: '点击“创建案件”后，系统会自动跳转至案件详情页。届时您可以在“证据”标签页中使用弹窗选择器（支持文件夹选取），一键批量上传您的全部证据材料。',
    submitLabel: '创建案件',
  },
  enterprise: {
    title: '新建法律事项',
    templateHeading: '选择企业法律事项',
    formTitle: '事项信息',
    titleLabel: '事项标题 *',
    titlePlaceholder: '例如：某客户拖欠货款催收、某合同付款条款审查',
    plaintiffLabel: '我方主体',
    plaintiffPlaceholder: '企业名称或经办部门',
    defendantLabel: '相对方',
    defendantPlaceholder: '客户、供应商、员工或合作方',
    amountLabel: '涉及金额',
    amountPlaceholder: '可选，填写合同额、欠款额或预计风险金额',
    descriptionLabel: '事项说明',
    descriptionPlaceholder: '说明业务背景、已发生的事实、目前想解决的问题和已采取行动',
    evidenceTitle: '企业材料留痕',
    evidenceDescription: '创建后优先上传合同、对账、审批、沟通和交付记录。系统输出用于风险识别和行动准备，高风险事项仍需专业复核。',
    submitLabel: '创建事项',
  },
  personal: {
    title: '新建法律问题',
    templateHeading: '选择个人法律问题',
    formTitle: '问题信息',
    titleLabel: '问题标题 *',
    titlePlaceholder: '例如：房东不退押金、公司拖欠工资、朋友借钱不还',
    plaintiffLabel: '我是谁',
    plaintiffPlaceholder: '可以填本人、家人或代称',
    defendantLabel: '对方是谁',
    defendantPlaceholder: '个人、公司、房东、平台或机构',
    amountLabel: '涉及金额',
    amountPlaceholder: '可选，不确定可以先不填',
    descriptionLabel: '发生了什么',
    descriptionPlaceholder: '不用专业术语，按时间顺序说清发生了什么、现在最担心什么',
    evidenceTitle: '先保住证据',
    evidenceDescription: '创建后先保存聊天、转账、合同、照片、录音、快递和投诉记录。系统会帮助你整理事实和下一步清单，不承诺结果，也不替你做最终决定。',
    submitLabel: '创建问题',
  },
};

function resolveAudience(tenantType?: TenantType): AudienceMode {
  if (tenantType === 'enterprise' || tenantType === 'personal') {
    return tenantType;
  }
  return 'law_firm';
}

export default function CaseNewPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tenantType = useAuthStore((s) => s.tenant?.tenant_type);
  const audience = resolveAudience(tenantType);
  const templates = templatesByAudience[audience];
  const copy = copyByAudience[audience];
  const initialTemplate = searchParams.get('template') ?? '';
  const [title, setTitle] = useState('');
  const [type, setType] = useState('');
  const [description, setDescription] = useState('');
  const [plaintiffName, setPlaintiffName] = useState('');
  const [defendantName, setDefendantName] = useState('');
  const [amount, setAmount] = useState('');
  const createCase = useCreateCase();

  useEffect(() => {
    if (initialTemplate && templates.some((template) => template.type === initialTemplate)) {
      setType(initialTemplate);
    }
  }, [initialTemplate, templates]);

  const selectedTemplate = useMemo(
    () => templates.find((template) => template.type === type),
    [templates, type]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        title,
        case_type: selectedTemplate?.caseType ?? 'civil',
        cause: selectedTemplate?.label,
        description,
        plaintiff: plaintiffName,
        defendant: defendantName,
        claim_amount: amount || undefined,
      } as unknown as Partial<Case>;
      const result = await createCase.mutateAsync(payload);
      navigate(`/cases/${result.id}`);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{copy.title}</h1>
        <Button variant="outline" onClick={() => navigate(-1)}>
          返回
        </Button>
      </div>

      <div className="mb-8">
        <h2 className="mb-4 text-lg font-semibold">{copy.templateHeading}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <CaseTemplateCard
              key={template.type}
              {...template}
              onSelect={() => setType(template.type)}
            />
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {copy.formTitle} {selectedTemplate && `(已选择: ${selectedTemplate.label})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>{copy.titleLabel}</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder={copy.titlePlaceholder} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label>{copy.plaintiffLabel}</Label>
                <Input value={plaintiffName} onChange={(e) => setPlaintiffName(e.target.value)} placeholder={copy.plaintiffPlaceholder} />
              </div>
              <div>
                <Label>{copy.defendantLabel}</Label>
                <Input value={defendantName} onChange={(e) => setDefendantName(e.target.value)} placeholder={copy.defendantPlaceholder} />
              </div>
            </div>
            <div>
              <Label>{copy.amountLabel}</Label>
              <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder={copy.amountPlaceholder} />
            </div>
            <div>
              <Label>{copy.descriptionLabel}</Label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder={copy.descriptionPlaceholder} />
            </div>

            <div className="rounded-lg border bg-muted/50 p-4">
              <h3 className="text-sm font-medium text-foreground">{copy.evidenceTitle}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{copy.evidenceDescription}</p>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" type="button" onClick={() => navigate(-1)}>
                取消
              </Button>
              <Button type="submit" disabled={createCase.isPending}>
                {createCase.isPending ? '创建中...' : copy.submitLabel}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
