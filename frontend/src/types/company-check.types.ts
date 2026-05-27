// 企业核查API类型

export interface CompanySearchParams {
  name?: string;
  creditCode?: string;      // 统一社会信用代码
  registrationNumber?: string;
}

export interface CompanyInfo {
  // 基本信息
  name: string;              // 企业名称
  creditCode: string;        // 统一社会信用代码
  registrationNumber: string; // 注册号
  legalPerson: string;       // 法定代表人
  registeredCapital: string; // 注册资本
  paidInCapital: string;     // 实缴资本
  
  // 状态信息
  status: string;           // 经营状态 (在业/注销/吊销等)
  establishmentDate: string; // 成立日期
  approvalDate: string;      // 核准日期
  businessTerm: string;      // 营业期限
  
  // 地址信息
  registeredAddress: string; // 注册地址
  actualAddress?: string;    // 实际经营地址
  
  // 经营范围
  businessScope: string;
  
  // 联系方式
  phone?: string;
  email?: string;
  website?: string;
  
  // 工商信息
  industry: string;          // 所属行业
  registrationAuthority: string; // 登记机关
  organizationType: string;  // 企业类型
  employeeCount?: string;   // 员工人数
  
  // 股东信息
  shareholders?: Shareholder[];
  
  // 变更记录
  changeRecords?: ChangeRecord[];
  
  // 风险信息
  risks?: CompanyRisk[];
  
  // 关联企业
  relatedCompanies?: RelatedCompany[];
  
  // 资质信息
  qualifications?: Qualification[];
  
  // Logo
  logoUrl?: string;
  
  // 来源
  source: string;
  queryTime: string;
}

export interface Shareholder {
  name: string;
  type: 'person' | 'company';
  contributionAmount?: string;
  contributionRatio?: string;
  paidAmount?: string;
}

export interface ChangeRecord {
  changeType: string;
  changeBefore?: string;
  changeAfter: string;
  changeDate: string;
}

export interface CompanyRisk {
  type: 'lawsuit' | 'execution' | 'tax' | 'credit' | 'administrative';
  level: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  date?: string;
  amount?: string;
}

export interface RelatedCompany {
  name: string;
  relationship: string;
  status: string;
}

export interface Qualification {
  name: string;
  number?: string;
  validUntil?: string;
  status: string;
}

// Logo API 响应
export interface CompanyLogoResult {
  companyName: string;
  logoUrl?: string;
  faviconUrl?: string;
  source: string;
}

// 联系方式验证
export interface ContactValidation {
  type: 'phone' | 'email' | 'website';
  value: string;
  isValid: boolean;
  validationDetails?: {
    reachable?: boolean;
    riskLevel?: 'low' | 'medium' | 'high';
    details?: string;
  };
}

// 企业对比
export interface CompanyComparison {
  companies: CompanyInfo[];
  comparisonItems: ComparisonItem[];
}

export interface ComparisonItem {
  field: string;
  label: string;
  values: Record<string, string>;
}

// 企业评分
export interface CompanyScore {
  overall: number;
  legalRisk: number;
  businessStability: number;
  financialHealth: number;
  creditRating: string;
  details: ScoreDetail[];
}

export interface ScoreDetail {
  category: string;
  score: number;
  factors: string[];
}
