// 对话V2类型定义 - 意图识别 + 澄清机制

export type IntentType = 
  | 'case_info'           // 案件信息查询
  | 'evidence_help'        // 证据帮助
  | 'document_generate'    // 文书草稿
  | 'deadline_query'       // 期限查询
  | 'law_search'           // 法律检索
  | 'strategy_advice'      // 策略建议
  | 'court_info'           // 法院信息
  | 'fee_calculation'      // 费用计算
  | 'procedure_guide'      // 程序指引
  | 'general_chat'         // 闲聊
  | 'clarification'        // 需要澄清
  | 'unknown';             // 未知意图

export interface IntentResult {
  intent: IntentType;
  confidence: number;      // 0-1
  entities: IntentEntity[];
  suggestions: string[];   // 建议选项
  requiresClarification: boolean;
  clarificationQuestions?: ClarificationQuestion[];
  suggestedActions?: SuggestedAction[];
}

export interface IntentEntity {
  type: 'person' | 'date' | 'amount' | 'court' | 'law' | 'document' | 'evidence';
  value: string;
  confidence: number;
}

export interface ClarificationQuestion {
  id: string;
  question: string;
  options?: ClarificationOption[];
  required: boolean;
  context: string;         // 为什么需要这个问题
}

export interface ClarificationOption {
  value: string;
  label: string;
  description?: string;
}

export interface SuggestedAction {
  id: string;
  type: 'generate_document' | 'search_evidence' | 'show_deadline' | 'search_law' | 'show_case_info';
  label: string;
  description: string;
  icon?: string;
  params?: Record<string, unknown>;
}

// 对话状态
export interface ChatState {
  intent: IntentResult | null;
  isProcessing: boolean;
  clarificationStep: number;
  conversationMode: 'normal' | 'guided' | 'clarification';
}

// 快速操作
export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  intent: IntentType;
  description: string;
  params?: Record<string, unknown>;
}

// 对话模板
export interface ChatTemplate {
  id: string;
  trigger: string[];
  intent: IntentType;
  response: string;
  followUp?: string;
}

// 意图映射
export const INTENT_LABELS: Record<IntentType, string> = {
  case_info: '案件信息',
  evidence_help: '证据帮助',
  document_generate: '文书草稿',
  deadline_query: '期限查询',
  law_search: '法律检索',
  strategy_advice: '策略建议',
  court_info: '法院信息',
  fee_calculation: '费用计算',
  procedure_guide: '程序指引',
  general_chat: '闲聊',
  clarification: '需要澄清',
  unknown: '未知',
};

export const INTENT_COLORS: Record<IntentType, string> = {
  case_info: 'bg-blue-100 text-blue-800',
  evidence_help: 'bg-purple-100 text-purple-800',
  document_generate: 'bg-green-100 text-green-800',
  deadline_query: 'bg-orange-100 text-orange-800',
  law_search: 'bg-cyan-100 text-cyan-800',
  strategy_advice: 'bg-indigo-100 text-indigo-800',
  court_info: 'bg-teal-100 text-teal-800',
  fee_calculation: 'bg-yellow-100 text-yellow-800',
  procedure_guide: 'bg-pink-100 text-pink-800',
  general_chat: 'bg-gray-100 text-gray-800',
  clarification: 'bg-amber-100 text-amber-800',
  unknown: 'bg-red-100 text-red-800',
};
