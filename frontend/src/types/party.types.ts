// 当事人类型定义

export interface Party {
  id: string;
  caseId: string;
  name: string;
  role: 'plaintiff' | 'defendant' | 'third_party' | 'counter_claimant' | 'counter_defendant';
  phone?: string;
  email?: string;
  address?: string;
  agent?: string;
  agentPhone?: string;
  relationship?: string;
  companyInfo?: CompanyInfo;
  createdAt: string;
  updatedAt: string;
}

export interface CompanyInfo {
  name: string;
  creditCode?: string;
  legalRepresentative?: string;
  registeredCapital?: string;
  status?: string;
}
