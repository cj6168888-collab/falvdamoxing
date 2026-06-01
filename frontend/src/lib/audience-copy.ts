import type { TenantType } from '@/types/auth';

export type AudienceMode = TenantType;

export interface AudienceLabels {
  workspaceSubtitle: string;
  caseNoun: string;
  caseList: string;
  newCase: string;
  searchPlaceholder: string;
  emptyTitle: string;
  emptyDescription: string;
  selectedUnit: string;
  plaintiffLabel: string;
  defendantLabel: string;
  amountLabel: string;
  batchArchiveDescription: string;
  detailWorkflowTitle: string;
  detailWorkflowDescription: string;
  overviewTab: string;
  chatTab: string;
  evidenceTab: string;
  analysisTab: string;
  reportsTab: string;
  timelineTab: string;
  lettersTab: string;
  documentsTab: string;
  partiesTab: string;
  executionTab: string;
  appealTab: string;
  profileTab: string;
  folderTab: string;
  evidenceGraph: string;
  evidenceGuide: string;
  insight: string;
  streamingAnalysis: string;
  hearing: string;
  progress: string;
}

const labelsByAudience: Record<AudienceMode, AudienceLabels> = {
  law_firm: {
    workspaceSubtitle: '法律工作辅助系统',
    caseNoun: '案件',
    caseList: '案件管理',
    newCase: '新建案件',
    searchPlaceholder: '搜索案件名称/当事人/案号...',
    emptyTitle: '暂无案件',
    emptyDescription: '点击新建案件开始',
    selectedUnit: '个案件',
    plaintiffLabel: '原告/申请人',
    defendantLabel: '被告/被执行人',
    amountLabel: '争议金额',
    batchArchiveDescription: '确定要将选中的 {count} 个案件归档吗？归档后的案件将标记为已关闭状态。',
    detailWorkflowTitle: '案件工作流',
    detailWorkflowDescription: '围绕证据目录、时间线、诉讼风险分析和文书草稿组织案件材料，优先输出律师可复核的工作成果。',
    overviewTab: '概览',
    chatTab: '法律 AI 助手',
    evidenceTab: '证据链',
    analysisTab: '诉讼风险分析',
    reportsTab: '报告',
    timelineTab: '时间线',
    lettersTab: '函件',
    documentsTab: '文书',
    partiesTab: '当事人',
    executionTab: '执行',
    appealTab: '上诉',
    profileTab: '画像',
    folderTab: '文件夹',
    evidenceGraph: '证据图谱',
    evidenceGuide: '补证引导',
    insight: '增强分析',
    streamingAnalysis: '流式分析',
    hearing: '庭审辅助',
    progress: '进度追踪',
  },
  enterprise: {
    workspaceSubtitle: '企业法律顾问工作台',
    caseNoun: '法律事项',
    caseList: '法律事项',
    newCase: '新建法律事项',
    searchPlaceholder: '搜索事项名称/相对方/经办部门...',
    emptyTitle: '暂无法律事项',
    emptyDescription: '点击新建法律事项开始',
    selectedUnit: '个事项',
    plaintiffLabel: '我方主体',
    defendantLabel: '相对方',
    amountLabel: '涉及金额',
    batchArchiveDescription: '确定要将选中的 {count} 个事项归档吗？归档后将标记为已关闭状态。',
    detailWorkflowTitle: '企业法律事项工作流',
    detailWorkflowDescription: '围绕合同、回款、用工、客户供应商争议和合规材料组织风险台账，优先输出可复核的行动清单和律师协作摘要。',
    overviewTab: '事项概览',
    chatTab: '法律顾问助手',
    evidenceTab: '材料留痕',
    analysisTab: '风险识别',
    reportsTab: '风险报告',
    timelineTab: '期限台账',
    lettersTab: '合同与函件',
    documentsTab: '文书草稿',
    partiesTab: '相关主体',
    executionTab: '回款跟踪',
    appealTab: '争议升级',
    profileTab: '事项画像',
    folderTab: '材料文件夹',
    evidenceGraph: '材料图谱',
    evidenceGuide: '材料缺口',
    insight: '深度分析',
    streamingAnalysis: '分析记录',
    hearing: '争议应对',
    progress: '行动跟踪',
  },
  personal: {
    workspaceSubtitle: '个人法律后盾',
    caseNoun: '法律问题',
    caseList: '我的法律问题',
    newCase: '新建法律问题',
    searchPlaceholder: '搜索问题名称/对方/关键词...',
    emptyTitle: '暂无法律问题',
    emptyDescription: '点击新建法律问题，先把事实和担心写下来',
    selectedUnit: '个问题',
    plaintiffLabel: '我',
    defendantLabel: '对方',
    amountLabel: '涉及金额',
    batchArchiveDescription: '确定要将选中的 {count} 个问题归档吗？归档后将标记为已关闭状态。',
    detailWorkflowTitle: '个人法律问题工作流',
    detailWorkflowDescription: '围绕事实时间线、证据保全、沟通记录、下一步清单和求助边界整理材料，先稳住处境，再逐步判断风险。',
    overviewTab: '问题概览',
    chatTab: '法律后盾助手',
    evidenceTab: '证据保全',
    analysisTab: '风险提示',
    reportsTab: '整理报告',
    timelineTab: '下一步',
    lettersTab: '沟通记录',
    documentsTab: '文书草稿',
    partiesTab: '相关人员',
    executionTab: '履行跟踪',
    appealTab: '救济路径',
    profileTab: '问题画像',
    folderTab: '材料文件夹',
    evidenceGraph: '材料关系',
    evidenceGuide: '补充材料',
    insight: '深度分析',
    streamingAnalysis: '分析记录',
    hearing: '应对准备',
    progress: '行动清单',
  },
};

export function getAudienceMode(tenantType?: TenantType | null): AudienceMode {
  if (tenantType === 'enterprise' || tenantType === 'personal') {
    return tenantType;
  }
  return 'law_firm';
}

export function getAudienceLabels(tenantType?: TenantType | null): AudienceLabels {
  return labelsByAudience[getAudienceMode(tenantType)];
}
