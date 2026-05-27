/**
 * 函件类型定义
 * 与后端 app/models/letter.py 完全对齐
 */

// 函件方向
export type LetterDirection = 'incoming' | 'outgoing';

// 函件类型
export type LetterType =
  | 'lawyer_letter'     // 律师函
  | 'demand_letter'     // 催告函/催款函
  | 'notice'            // 通知书
  | 'response'          // 回复函
  | 'reminder'          // 提醒函
  | 'warning'           // 警告函
  | 'negotiation'       // 协商函
  | 'explanation'       // 说明函
  | 'other';            // 其他

// 回复要求
export type ReplyRequirement =
  | 'required'          // 必须回复
  | 'recommended'        // 建议回复
  | 'optional'          // 可选回复
  | 'not_required'      // 不需要回复
  | 'deadline_passed';  // 已超期

// 紧急程度
export type UrgentLevel =
  | 'critical'  // 紧急（需立即处理）
  | 'high'       // 高（需当日处理）
  | 'medium'     // 中（3日内处理）
  | 'low'        // 低（7日内处理）
  | 'none';      // 无期限

// 邮寄状态
export type MailStatus =
  | 'draft'           // 草稿
  | 'draft_confirmed' // 草稿已确认
  | 'sending'         // 邮寄中
  | 'sent'            // 已发出
  | 'delivered'       // 已送达
  | 'read'            // 已阅读
  | 'replied';        // 已回复

// 回函类型
export type ReplyType = 'accept' | 'reject' | 'counter' | 'procedural' | 'other';

// 函件主体
export interface Letter {
  id: number;
  case_id: number;

  // 函件基本信息
  direction: LetterDirection;
  letter_type: LetterType;

  // 函件标识
  title: string;
  reference_number?: string;
  sender?: string;
  recipient?: string;

  // 日期信息
  letter_date?: string;       // 函件日期（落款日期）
  received_date?: string;    // 收到日期
  deadline?: string;          // 回复截止日期
  responded_date?: string;    // 回复日期

  // 回复要求分析
  reply_required: ReplyRequirement;
  reply_requirement_reason?: string;
  response_deadline_days?: number;
  legal_basis?: string;

  // 紧急程度
  urgent_level: UrgentLevel;
  is_overdue: boolean;
  days_until_deadline?: number;

  // 内容摘要
  content_summary?: string;
  key_demands?: string;
  risks?: string;

  // 回复状态
  is_replied: boolean;
  reply_content?: string;
  reply_approved?: boolean;
  draft_reply?: string;

  // 邮寄状态
  mail_status: MailStatus;
  mail_sent_date?: string;
  mail_delivered_date?: string;

  // 运单信息
  tracking_number?: string;
  courier_company?: string;

  // 邮寄目的
  mailing_purpose?: string;

  // 回执上传
  proof_of_delivery?: Array<{
    file: string;
    upload_date: string;
    type: string;
  }>;
  signature_image?: string;

  // 对方回函
  has_reply: boolean;
  reply_type?: ReplyType;
  reply_summary?: string;
  reply_document?: Array<{
    name: string;
    path: string;
  }>;

  // AI分析
  reply_analysis?: string;

  // 关联
  related_letter_id?: number;
  related_document_id?: number;
  related_evidence_ids?: number[];

  // 附件
  attachments?: Array<{
    name: string;
    path: string;
  }>;

  // 生成前备注
  generation_notes?: string;

  // 元数据
  created_at: string;
  updated_at: string;
}

// 创建函件请求
export interface CreateLetterRequest {
  direction: LetterDirection;
  letter_type: LetterType;
  title: string;
  reference_number?: string;
  sender?: string;
  recipient?: string;
  letter_date?: string;
  received_date?: string;
  deadline?: string;
  content_summary?: string;
  key_demands?: string;
  mailing_purpose?: string;
  generation_notes?: string;
}

// 更新函件请求
export interface UpdateLetterRequest extends Partial<CreateLetterRequest> {
  reply_required?: ReplyRequirement;
  reply_requirement_reason?: string;
  response_deadline_days?: number;
  legal_basis?: string;
  urgent_level?: UrgentLevel;
  draft_reply?: string;
  mail_status?: MailStatus;
  mail_sent_date?: string;
  mail_delivered_date?: string;
  tracking_number?: string;
  courier_company?: string;
  proof_of_delivery?: Array<{
    file: string;
    upload_date: string;
    type: string;
  }>;
  has_reply?: boolean;
  reply_type?: ReplyType;
  reply_summary?: string;
  reply_analysis?: string;
}

// 邮寄信息
export interface MailingInfo {
  courier_company?: string;
  tracking_number?: string;
  mailing_purpose?: string;
}

// 回函信息
export interface ReplyInfo {
  has_reply: boolean;
  reply_type?: ReplyType;
  reply_summary?: string;
  reply_document?: Array<{
    name: string;
    path: string;
  }>;
}

// 函件类型选项（用于下拉选择）
export const LETTER_TYPE_OPTIONS: Array<{ value: LetterType; label: string }> = [
  { value: 'lawyer_letter', label: '律师函' },
  { value: 'demand_letter', label: '催告函/催款函' },
  { value: 'notice', label: '通知书' },
  { value: 'response', label: '回复函' },
  { value: 'reminder', label: '提醒函' },
  { value: 'warning', label: '警告函' },
  { value: 'negotiation', label: '协商函' },
  { value: 'explanation', label: '说明函' },
  { value: 'other', label: '其他' },
];

// 方向选项
export const DIRECTION_OPTIONS: Array<{ value: LetterDirection; label: string }> = [
  { value: 'incoming', label: '收件' },
  { value: 'outgoing', label: '发件' },
];

// 紧急程度选项
export const URGENT_LEVEL_OPTIONS: Array<{ value: UrgentLevel; label: string; color: string }> = [
  { value: 'critical', label: '紧急', color: 'bg-red-500' },
  { value: 'high', label: '高', color: 'bg-orange-500' },
  { value: 'medium', label: '中', color: 'bg-yellow-500' },
  { value: 'low', label: '低', color: 'bg-green-500' },
  { value: 'none', label: '无期限', color: 'bg-gray-500' },
];

// 邮寄状态选项
export const MAIL_STATUS_OPTIONS: Array<{ value: MailStatus; label: string }> = [
  { value: 'draft', label: '草稿' },
  { value: 'draft_confirmed', label: '草稿已确认' },
  { value: 'sending', label: '邮寄中' },
  { value: 'sent', label: '已发出' },
  { value: 'delivered', label: '已送达' },
  { value: 'read', label: '已阅读' },
  { value: 'replied', label: '已回复' },
];

// 回函类型选项
export const REPLY_TYPE_OPTIONS: Array<{ value: ReplyType; label: string }> = [
  { value: 'accept', label: '接受' },
  { value: 'reject', label: '拒绝' },
  { value: 'counter', label: '反要约' },
  { value: 'procedural', label: '程序性回复' },
  { value: 'other', label: '其他' },
];

// 回复要求选项
export const REPLY_REQUIREMENT_OPTIONS: Array<{ value: ReplyRequirement; label: string }> = [
  { value: 'required', label: '必须回复' },
  { value: 'recommended', label: '建议回复' },
  { value: 'optional', label: '可选回复' },
  { value: 'not_required', label: '不需要回复' },
  { value: 'deadline_passed', label: '已超期' },
];
