// 法律案件追踪系统 - 常量定义

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8002';

export const CASE_STATUS = {
  PREPARING: 'preparing',
  NEGOTIATING: 'negotiating',
  LITIGATING: 'litigating',
  APPEALING: 'appealing',
  EXECUTING: 'executing',
  CLOSED: 'closed',
} as const;

export const CASE_TYPES = {
  LOAN: 'loan',
  CONTRACT: 'contract',
  TORT: 'tort',
  LABOR: 'labor',
  MARRIAGE: 'marriage',
  PROPERTY: 'property',
  OTHER: 'other',
} as const;

export const URGENCY_LEVELS = {
  EXPIRED: 'expired',
  URGENT: 'urgent',
  WARNING: 'warning',
  NORMAL: 'normal',
} as const;

export const PARTY_ROLES = {
  PLAINTIFF: 'plaintiff',
  DEFENDANT: 'defendant',
  THIRD_PARTY: 'third_party',
  COUNTER_CLAIMANT: 'counter_claimant',
  COUNTER_DEFENDANT: 'counter_defendant',
} as const;

export const EVIDENCE_TYPES = {
  CONTRACT: 'contract',
  RECEIPT: 'receipt',
  LETTER: 'letter',
  IDENTITY: 'identity',
  COMMUNICATION: 'communication',
  WITNESS: 'witness',
  EXPERT: 'expert',
  AUDIO_VIDEO: 'audio_video',
  OTHER: 'other',
} as const;

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

export const DATE_FORMAT = {
  CHINESE: 'yyyy 年 M 月 d 日',
  CHINESE_WITH_TIME: 'yyyy 年 M 月 d 日 HH:mm',
  ISO: 'yyyy-MM-dd',
  ISO_WITH_TIME: 'yyyy-MM-dd HH:mm:ss',
} as const;
