import type { TenantType } from '@/types/auth';
import {
  BriefcaseBusiness,
  Building2,
  FileCheck2,
  HeartHandshake,
  LucideIcon,
  ShieldCheck,
  UserRound,
} from 'lucide-react';

export type PublicAudience = TenantType;

export const audienceSlugs: Record<PublicAudience, string> = {
  law_firm: 'law-firm',
  enterprise: 'enterprise',
  personal: 'personal',
};

export const slugToAudience: Record<string, PublicAudience> = {
  'law-firm': 'law_firm',
  enterprise: 'enterprise',
  personal: 'personal',
};

export interface AudiencePublicCopy {
  type: PublicAudience;
  slug: string;
  label: string;
  icon: LucideIcon;
  eyebrow: string;
  headline: string;
  subhead: string;
  loginTitle: string;
  registerTitle: string;
  workspaceLabel: string;
  workspacePlaceholder: string;
  primaryCta: string;
  secondaryCta: string;
  previewTitle: string;
  previewItems: string[];
  benefits: string[];
  accentClass: string;
}

export const audiencePublicCopy: Record<PublicAudience, AudiencePublicCopy> = {
  law_firm: {
    type: 'law_firm',
    slug: 'law-firm',
    label: '律所',
    icon: Building2,
    eyebrow: '律所案件工作台',
    headline: '可复核的案件 AI 工作底稿',
    subhead: '围绕事实、证据链、争议焦点和诉讼风险，帮助律师团队形成可检查、可协作的办案底稿。',
    loginTitle: '进入案件工作台',
    registerTitle: '创建律所工作空间',
    workspaceLabel: '律所名称',
    workspacePlaceholder: '例如：甲鼎律师事务所',
    primaryCta: '律所使用',
    secondaryCta: '查看律所入口',
    previewTitle: '案件工作流',
    previewItems: ['案件总览', '证据链', '争议焦点', '庭审节点', '律师复核'],
    benefits: ['案件和材料统一留痕', '证据目录自动梳理', '对方视角反驳风险', '文书草稿保留依据'],
    accentClass: 'text-sky-700 bg-sky-50 border-sky-200',
  },
  enterprise: {
    type: 'enterprise',
    slug: 'enterprise',
    label: '企业',
    icon: BriefcaseBusiness,
    eyebrow: '企业法律顾问台',
    headline: '让任何企业拥有靠谱的法律顾问',
    subhead: '把合同、回款、劳动人事和经营风险放进同一个台账，先看清问题，再决定内部处理或外部律师复核。',
    loginTitle: '进入企业法律顾问台',
    registerTitle: '创建企业法律顾问空间',
    workspaceLabel: '企业名称',
    workspacePlaceholder: '例如：XX科技有限公司',
    primaryCta: '企业使用',
    secondaryCta: '查看企业入口',
    previewTitle: '企业事项流',
    previewItems: ['合同审查', '回款催告', '劳动人事', '风险台账', '律师协作清单'],
    benefits: ['合同履行节点留痕', '催告和回款动作清晰', '劳动人事风险提示', '外部律师协作摘要'],
    accentClass: 'text-teal-700 bg-teal-50 border-teal-200',
  },
  personal: {
    type: 'personal',
    slug: 'personal',
    label: '个人',
    icon: UserRound,
    eyebrow: '个人法律后盾',
    headline: '做你的法律后盾，先帮你稳住局面',
    subhead: '面对法律事务时，先保存证据、理清事实、看清风险，再拆出今天能做的下一步。',
    loginTitle: '进入我的法律后盾',
    registerTitle: '创建个人法律后盾空间',
    workspaceLabel: '个人空间名称',
    workspacePlaceholder: '例如：张三的法律后盾',
    primaryCta: '个人使用',
    secondaryCta: '查看个人入口',
    previewTitle: '个人行动流',
    previewItems: ['保存证据', '事实时间线', '风险提示', '今天先做什么', '克制沟通话术'],
    benefits: ['先稳住情绪和处境', '重要证据及时保存', '用普通话解释风险', '给出清楚行动清单'],
    accentClass: 'text-indigo-700 bg-indigo-50 border-indigo-200',
  },
};

export const publicSiteHighlights = [
  { icon: FileCheck2, title: '材料有来源', text: '每一条分析都尽量回到事实、材料和证据编号。' },
  { icon: ShieldCheck, title: '判断有边界', text: 'AI 不替代律师和专业判断，重要事项保留复核入口。' },
  { icon: HeartHandshake, title: '行动有顺序', text: '把风险、缺口和下一步拆成用户能执行的清单。' },
];

export function audienceFromSlug(slug?: string): PublicAudience | undefined {
  if (!slug) return undefined;
  return slugToAudience[slug];
}

