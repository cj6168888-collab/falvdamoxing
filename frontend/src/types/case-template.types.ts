// 案件模板类型定义

export interface CaseTemplate {
  id: string;
  name: string;
  type: string;
  description: string;
  icon: string;
  color: string;
  category: 'civil' | 'criminal' | 'labor' | 'commercial' | 'other';
  fields: TemplateField[];
  recommendedEvidence: string[];
  recommendedDocuments: string[];
  autoFillFields: string[];
  relatedLaws: string[];
  deadlines: DeadlineTemplate[];
}

export interface TemplateField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'textarea' | 'party';
  required: boolean;
  placeholder?: string;
  options?: SelectOption[];
  validation?: FieldValidation;
  autoFill?: string;
}

export interface SelectOption {
  value: string;
  label: string;
}

export interface FieldValidation {
  min?: number;
  max?: number;
  pattern?: string;
  message?: string;
}

export interface DeadlineTemplate {
  id: string;
  name: string;
  type: 'filing' | 'response' | 'appeal' | 'execution';
  daysFromStart: number;
  description: string;
  isCritical: boolean;
}

export interface CaseTemplateCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  templates: CaseTemplate[];
}

// 预设模板
export const CASE_TEMPLATES: CaseTemplate[] = [
  {
    id: 'template-debt',
    name: '民间借贷纠纷',
    type: 'debt_dispute',
    description: '适用于自然人之间的借贷纠纷案件',
    icon: '💰',
    color: 'text-emerald-600',
    category: 'civil',
    fields: [
      { key: 'plaintiff', label: '原告', type: 'party', required: true, placeholder: '原告姓名/名称' },
      { key: 'plaintiff_id', label: '原告身份证号', type: 'text', required: false, placeholder: '身份证号码' },
      { key: 'defendant', label: '被告', type: 'party', required: true, placeholder: '被告姓名/名称' },
      { key: 'defendant_id', label: '被告身份证号', type: 'text', required: false, placeholder: '身份证号码' },
      { key: 'loan_amount', label: '借款金额', type: 'number', required: true, placeholder: '请输入借款金额', validation: { min: 0 } },
      { key: 'loan_date', label: '借款日期', type: 'date', required: true },
      { key: 'due_date', label: '约定还款日期', type: 'date', required: false },
      { key: 'interest_rate', label: '约定利率(%)', type: 'number', required: false, placeholder: '年利率', validation: { min: 0, max: 36 } },
      { key: 'actual_interest_rate', label: '实际利率(%)', type: 'number', required: false, placeholder: '实际执行的利率' },
      { key: 'court', label: '管辖法院', type: 'select', required: true, 
        options: [
          { value: '', label: '请选择法院' },
          { value: 'beijing_chengyang', label: '北京市朝阳区人民法院' },
          { value: 'beijing_haidian', label: '北京市海淀区人民法院' },
          { value: 'shanghai_pudong', label: '上海市浦东新区人民法院' },
          { value: 'shenzhen_futian', label: '深圳市福田区人民法院' },
        ]
      },
      { key: 'description', label: '案情描述', type: 'textarea', required: false, placeholder: '简要描述借贷事实...' },
    ],
    recommendedEvidence: [
      '借条/欠条原件',
      '银行转账记录',
      '微信/支付宝转账截图',
      '聊天记录截图',
      '证人证言',
      '还款记录',
    ],
    recommendedDocuments: [
      '民事起诉状',
      '证据清单',
      '当事人身份证明',
      '授权委托书',
    ],
    autoFillFields: ['title', 'type', 'description'],
    relatedLaws: [
      '《民法典》第六百六十七条',
      '《民法典》第六百六十八条',
      '《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》',
    ],
    deadlines: [
      { id: 'd1', name: '立案', type: 'filing', daysFromStart: 0, description: '提交起诉材料', isCritical: true },
      { id: 'd2', name: '举证期限', type: 'response', daysFromStart: 15, description: '提交证据材料', isCritical: false },
      { id: 'd3', name: '答辩期限', type: 'response', daysFromStart: 15, description: '被告提交答辩状', isCritical: false },
    ],
  },
  {
    id: 'template-contract',
    name: '合同纠纷',
    type: 'contract_dispute',
    description: '适用于各类合同争议案件',
    icon: '📄',
    color: 'text-blue-600',
    category: 'commercial',
    fields: [
      { key: 'plaintiff', label: '原告/申请方', type: 'party', required: true },
      { key: 'defendant', label: '被告/被申请方', type: 'party', required: true },
      { key: 'contract_type', label: '合同类型', type: 'select', required: true,
        options: [
          { value: 'sale', label: '买卖合同' },
          { value: 'lease', label: '租赁合同' },
          { value: 'loan', label: '借款合同' },
          { value: 'service', label: '服务合同' },
          { value: 'construction', label: '建设工程合同' },
          { value: 'other', label: '其他合同' },
        ]
      },
      { key: 'contract_amount', label: '合同金额', type: 'number', required: true, validation: { min: 0 } },
      { key: 'contract_date', label: '签订日期', type: 'date', required: true },
      { key: 'breach_description', label: '违约情况', type: 'textarea', required: true, placeholder: '描述对方的违约行为...' },
      { key: 'claim_amount', label: '诉讼请求金额', type: 'number', required: false, validation: { min: 0 } },
      { key: 'court', label: '管辖法院', type: 'select', required: true },
      { key: 'description', label: '案情描述', type: 'textarea', required: false },
    ],
    recommendedEvidence: [
      '合同原件',
      '合同变更协议',
      '履约凭证',
      '往来函件',
      '付款凭证',
      '违约通知函',
    ],
    recommendedDocuments: [
      '民事起诉状',
      '证据清单',
      '合同复印件',
      '授权委托书',
    ],
    autoFillFields: ['title', 'type', 'description'],
    relatedLaws: [
      '《民法典》第五百零九条',
      '《民法典》第五百七十七条',
      '《民法典》第五百八十四条',
    ],
    deadlines: [
      { id: 'd1', name: '立案', type: 'filing', daysFromStart: 0, description: '提交起诉材料', isCritical: true },
      { id: 'd2', name: '举证期限', type: 'response', daysFromStart: 15, description: '提交证据材料', isCritical: false },
    ],
  },
  {
    id: 'template-labor',
    name: '劳动争议',
    type: 'labor_dispute',
    description: '适用于劳动仲裁和劳动诉讼案件',
    icon: '👷',
    color: 'text-orange-600',
    category: 'labor',
    fields: [
      { key: 'plaintiff', label: '申请人(劳动者)', type: 'party', required: true },
      { key: 'defendant', label: '被申请人(单位)', type: 'party', required: true },
      { key: 'defendant_company', label: '公司名称', type: 'text', required: true },
      { key: 'labor_type', label: '争议类型', type: 'select', required: true,
        options: [
          { value: 'wage', label: '工资报酬' },
          { value: 'economic_compensation', label: '经济补偿' },
          { value: 'insurance', label: '社会保险' },
          { value: 'termination', label: '违法解除' },
          { value: 'overtime', label: '加班工资' },
          { value: 'other', label: '其他' },
        ]
      },
      { key: 'work_start_date', label: '入职日期', type: 'date', required: false },
      { key: 'work_end_date', label: '离职日期', type: 'date', required: false },
      { key: 'monthly_salary', label: '月工资标准', type: 'number', required: false, validation: { min: 0 } },
      { key: 'claim_amount', label: '仲裁请求金额', type: 'number', required: false, validation: { min: 0 } },
      { key: 'description', label: '案情描述', type: 'textarea', required: false },
    ],
    recommendedEvidence: [
      '劳动合同',
      '工资条/银行流水',
      '社保缴纳记录',
      '解除劳动合同通知书',
      '工作证/工牌',
      '同事证言',
    ],
    recommendedDocuments: [
      '劳动仲裁申请书',
      '证据清单',
      '劳动合同复印件',
      '授权委托书',
    ],
    autoFillFields: ['title', 'type', 'description'],
    relatedLaws: [
      '《劳动合同法》第十条',
      '《劳动合同法》第三十八条',
      '《劳动合同法》第四十六条',
    ],
    deadlines: [
      { id: 'd1', name: '仲裁申请', type: 'filing', daysFromStart: 0, description: '向劳动仲裁委提交申请', isCritical: true },
    ],
  },
  {
    id: 'template-tort',
    name: '侵权纠纷',
    type: 'tort_dispute',
    description: '适用于人身损害赔偿、财产损害等侵权案件',
    icon: '⚖️',
    color: 'text-purple-600',
    category: 'civil',
    fields: [
      { key: 'plaintiff', label: '原告(受害人)', type: 'party', required: true },
      { key: 'defendant', label: '被告(侵权人)', type: 'party', required: true },
      { key: 'tort_type', label: '侵权类型', type: 'select', required: true,
        options: [
          { value: 'traffic', label: '交通事故' },
          { value: 'medical', label: '医疗损害' },
          { value: 'work_injury', label: '工伤事故' },
          { value: 'product', label: '产品责任' },
          { value: 'environmental', label: '环境污染' },
          { value: 'other', label: '其他侵权' },
        ]
      },
      { key: 'incident_date', label: '侵权发生日期', type: 'date', required: true },
      { key: 'incident_location', label: '侵权发生地点', type: 'text', required: true },
      { key: 'damage_amount', label: '损失金额', type: 'number', required: true, validation: { min: 0 } },
      { key: 'liability_ratio', label: '责任比例(%)', type: 'number', required: false, validation: { min: 0, max: 100 } },
      { key: 'description', label: '案情描述', type: 'textarea', required: true },
    ],
    recommendedEvidence: [
      '事故现场照片/视频',
      '责任认定书',
      '医疗记录/诊断证明',
      '医疗费用票据',
      '收入证明',
      '伤残鉴定报告',
    ],
    recommendedDocuments: [
      '民事起诉状',
      '证据清单',
      '责任认定书复印件',
      '医疗票据复印件',
    ],
    autoFillFields: ['title', 'type', 'description'],
    relatedLaws: [
      '《民法典》第一千一百六十五条',
      '《民法典》第一千一百七十九条',
      '《民法典》第一千一百八十三条',
    ],
    deadlines: [
      { id: 'd1', name: '立案', type: 'filing', daysFromStart: 0, description: '提交起诉材料', isCritical: true },
      { id: 'd2', name: '鉴定申请', type: 'response', daysFromStart: 7, description: '申请伤残鉴定', isCritical: false },
    ],
  },
  {
    id: 'template-divorce',
    name: '离婚纠纷',
    type: 'divorce_dispute',
    description: '适用于离婚及财产分割、子女抚养争议案件',
    icon: '💔',
    color: 'text-pink-600',
    category: 'civil',
    fields: [
      { key: 'plaintiff', label: '原告', type: 'party', required: true },
      { key: 'defendant', label: '被告', type: 'party', required: true },
      { key: 'marriage_date', label: '结婚日期', type: 'date', required: true },
      { key: 'separation_date', label: '分居日期', type: 'date', required: false },
      { key: 'has_children', label: '是否有子女', type: 'select', required: true,
        options: [
          { value: 'yes', label: '有' },
          { value: 'no', label: '无' },
        ]
      },
      { key: 'children_count', label: '子女数量', type: 'number', required: false, validation: { min: 0 } },
      { key: 'divorce_reason', label: '离婚原因', type: 'textarea', required: true },
      { key: 'property_dispute', label: '财产分割争议', type: 'textarea', required: false },
      { key: 'child_custody', label: '子女抚养争议', type: 'textarea', required: false },
      { key: 'description', label: '其他情况', type: 'textarea', required: false },
    ],
    recommendedEvidence: [
      '结婚证',
      '身份证/户口本',
      '子女出生证明',
      '财产证明文件',
      '感情破裂证据',
      '分居证据',
    ],
    recommendedDocuments: [
      '民事起诉状',
      '证据清单',
      '结婚证复印件',
      '财产清单',
    ],
    autoFillFields: ['title', 'type', 'description'],
    relatedLaws: [
      '《民法典》第一千零七十九条',
      '《民法典》第一千零八十四条',
      '《民法典》第一千零八十七条',
    ],
    deadlines: [
      { id: 'd1', name: '立案', type: 'filing', daysFromStart: 0, description: '提交起诉材料', isCritical: true },
      { id: 'd2', name: '答辩期限', type: 'response', daysFromStart: 15, description: '被告提交答辩状', isCritical: false },
    ],
  },
];

// 模板分类
export const CASE_TEMPLATE_CATEGORIES: CaseTemplateCategory[] = [
  {
    id: 'civil',
    name: '民事案件',
    icon: '⚖️',
    description: '民事纠纷类案件',
    templates: CASE_TEMPLATES.filter(t => t.category === 'civil'),
  },
  {
    id: 'commercial',
    name: '商事案件',
    icon: '🏢',
    description: '商业合同类案件',
    templates: CASE_TEMPLATES.filter(t => t.category === 'commercial'),
  },
  {
    id: 'labor',
    name: '劳动案件',
    icon: '👷',
    description: '劳动争议类案件',
    templates: CASE_TEMPLATES.filter(t => t.category === 'labor'),
  },
  {
    id: 'other',
    name: '其他案件',
    icon: '📋',
    description: '其他类型案件',
    templates: CASE_TEMPLATES.filter(t => t.category === 'other'),
  },
];

// 获取模板
export function getTemplate(id: string): CaseTemplate | undefined {
  return CASE_TEMPLATES.find(t => t.id === id);
}

// 根据类型获取模板
export function getTemplateByType(type: string): CaseTemplate | undefined {
  return CASE_TEMPLATES.find(t => t.type === type);
}

// 自动填充标题
export function generateCaseTitle(template: CaseTemplate, parties: { plaintiff?: string; defendant?: string }): string {
  const plaintiff = parties.plaintiff || '原告';
  const defendant = parties.defendant || '被告';
  const templateName = template.name.replace('纠纷', '').replace('案件', '');
  return `${plaintiff}诉${defendant}${templateName}案`;
}
