// 报告类型
export interface Report {
  id: string;
  caseId: string;
  type: 'case_analysis' | 'litigation_strategy' | 'full_analysis' | 'evidence_report' | 'milestone_report' | 'opponent_analysis';
  title: string;
  status: 'generating' | 'completed' | 'failed';
  progress?: number;
  content?: string;
  sections?: string[];
  createdAt: string;
  updatedAt: string;
}

// 报告大纲 - 与后端 ReportOutline.to_dict() 对应
export interface ReportOutline {
  id: string;
  case_id: number;
  report_type: string; // ANALYSIS, STRATEGY, FULL_ANALYSIS, EVIDENCE_REPORT, MILESTONE_REPORT, OPPONENT_ANALYSIS
  report_type_name: string;
  report_type_icon: string;
  title: string;
  description: string;
  status: string; // PLANNING, GENERATING, VALIDATING, COMPLETED, PARTIAL, FAILED
  progress: ReportProgress;
  total_tokens: number;
  processing_time: number;
  version: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

// 报告进度 - 与后端 get_progress() 对应
export interface ReportProgress {
  total: number;
  completed: number;
  failed: number;
  progress: number;
  status: string;
}

// 报告详情 - 包含章节列表
export interface ReportDetail extends ReportOutline {
  sections: ReportSection[];
  total_sections: number;
  completed_sections: number;
}

// 报告章节 - 与后端 ReportSection.to_full_dict() 对应
export interface ReportSection {
  id: string;
  outline_id: string;
  section_index: number;
  title: string;
  subtitle?: string;
  content: string;
  summary?: string;
  key_points: unknown[];
  status: string;
  created_at: string;
  completed_at: string | null;
}

// 报告生成请求
export interface GenerateReportRequest {
  caseId: string;
  type: ReportType;
  forceRegenerate?: boolean;
}

// 报告类型枚举
export type ReportType =
  | 'analysis'      // 案件分析
  | 'strategy'      // 策略建议
  | 'full_analysis' // 完整对抗性分析
  | 'evidence'      // 证据报告
  | 'milestone'     // 里程碑报告
  | 'summary';      // 案件总结

// 报告状态
export type ReportStatusType =
  | 'PLANNING'
  | 'GENERATING'
  | 'VALIDATING'
  | 'COMPLETED'
  | 'PARTIAL'
  | 'FAILED';

// 导出格式类型
export type ExportFormat = 'markdown' | 'text' | 'pdf' | 'word';

// 导出格式配置
export const EXPORT_FORMAT_CONFIG: Record<ExportFormat, {
  label: string;
  extension: string;
  mimeType: string;
  available: boolean;
}> = {
  'markdown': { label: 'Markdown 格式', extension: '.md', mimeType: 'text/markdown', available: true },
  'text': { label: '纯文本格式', extension: '.txt', mimeType: 'text/plain', available: true },
  'pdf': { label: 'PDF 文档', extension: '.pdf', mimeType: 'application/pdf', available: true },
  'word': { label: 'Word 文档', extension: '.docx', mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', available: true },
};

// 报告对比结果
export interface ReportCompareResult {
  report_1: {
    id: string;
    title: string;
    report_type: string;
    version: number;
    created_at: string | null;
    sections_count: number;
  };
  report_2: {
    id: string;
    title: string;
    report_type: string;
    version: number;
    created_at: string | null;
    sections_count: number;
  };
  section_comparison: Array<{
    index: number;
    status: 'both' | 'only_first' | 'only_second';
    section_1?: {
      title: string;
      content_length: number;
      completed_at: string | null;
    };
    section_2?: {
      title: string;
      content_length: number;
      completed_at: string | null;
    };
    similarity: number | null;
  }>;
  summary: {
    total_sections: number;
    common_sections: number;
    only_in_first: number;
    only_in_second: number;
  };
}

// 报告类型配置
export const REPORT_TYPE_CONFIG: Record<string, {
  label: string;
  color: string;
  icon: string;
  description: string;
}> = {
  'ANALYSIS': {
    label: '案件分析',
    color: 'bg-blue-500',
    icon: 'BarChart3',
    description: '全面分析案件事实和法律问题'
  },
  'STRATEGY': {
    label: '策略建议',
    color: 'bg-green-500',
    icon: 'Target',
    description: '诉讼策略和行动建议'
  },
  'FULL_ANALYSIS': {
    label: '完整对抗性分析',
    color: 'bg-purple-500',
    icon: 'Shield',
    description: '双方视角的完整对抗性分析'
  },
  'EVIDENCE_REPORT': {
    label: '证据报告',
    color: 'bg-orange-500',
    icon: 'FileText',
    description: '证据梳理和分析报告'
  },
  'MILESTONE_REPORT': {
    label: '里程碑报告',
    color: 'bg-teal-500',
    icon: 'Calendar',
    description: '案件进度和待办事项'
  },
  'OPPONENT_ANALYSIS': {
    label: '对手分析',
    color: 'bg-red-500',
    icon: 'User',
    description: '对手策略和弱点分析'
  }
};

// 报告状态配置
export const REPORT_STATUS_CONFIG: Record<string, {
  label: string;
  variant: 'default' | 'secondary' | 'destructive' | 'outline' | null;
}> = {
  'PLANNING': { label: '规划中', variant: 'secondary' },
  'GENERATING': { label: '生成中', variant: 'secondary' },
  'VALIDATING': { label: '校验中', variant: 'secondary' },
  'COMPLETED': { label: '已完成', variant: 'default' },
  'PARTIAL': { label: '部分完成', variant: 'outline' },
  'FAILED': { label: '失败', variant: 'destructive' }
};
