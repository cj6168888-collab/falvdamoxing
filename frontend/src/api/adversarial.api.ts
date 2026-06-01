import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';

export function useAdversarialAnalysis(caseId: string) {
  return useQuery({
    queryKey: ['adversarial', caseId],
    queryFn: () => axiosInstance.get(`/api/adversarial/case/${caseId}/analyses`).then(res => res.data),
    enabled: !!caseId,
  });
}

export async function createAnalysis(caseId: string, data: unknown) {
  return axiosInstance.post(`/api/adversarial/case/${caseId}/analysis`, data).then(res => res.data);
}

export async function generateEvidenceMatrix(caseId: string) {
  return axiosInstance.post(`/api/adversarial/case/${caseId}/evidence-matrix`).then(res => res.data);
}

export async function predictScenarios(caseId: string) {
  return axiosInstance.post(`/api/adversarial/case/${caseId}/scenario-prediction`).then(res => res.data);
}

export async function opponentAnalysis(caseId: string) {
  return axiosInstance.post(`/api/adversarial/case/${caseId}/opponent-analysis`).then(res => res.data);
}

// ============ 流式辩论 API ============

export interface DebateRound {
  round: number;
  speaker: string;
  content: string;
  thinking: string;
  timestamp: string;
}

export interface DebateProgress {
  debate_id: string;
  status: 'not_found' | 'started' | 'in_progress' | 'completed' | 'failed';
  current_round: number;
  rounds: DebateRound[];
  current_thinking: Record<string, string>;
  final_report: string | null;
  analysis_id?: number;
  error?: string | null;
  warning?: string | null;
  started_at: string;
  completed_at?: string;
}

export interface DebateRequest {
  分析阶段?: string;
  analysis_phase?: string;
  对手名称?: string;
  对手类型?: string;
  我方证据?: string;
  对方证据?: string;
  辩论轮数?: number;
  user_input?: string;
}

/**
 * 启动流式辩论
 * @returns debate_id 用于轮询进度
 */
export async function startDebateStream(caseId: string, data?: Partial<DebateRequest>): Promise<{ debate_id: string; status: string; message: string }> {
  return axiosInstance.post(`/api/adversarial/case/${caseId}/debate-stream`, data || {}).then(res => res.data);
}

/**
 * 获取辩论进度
 * @param debateId 辩论ID
 * @returns 辩论进度状态
 */
export async function getDebateProgress(debateId: string): Promise<DebateProgress> {
  return axiosInstance.get(`/api/adversarial/debate/${debateId}/progress`).then(res => res.data);
}

/**
 * 继续辩论（用户参与）
 * @param debateId 辩论ID
 * @param userInput 用户输入
 */
export async function continueDebate(debateId: string, userInput: string): Promise<{ response: string }> {
  return axiosInstance.post(`/api/adversarial/debate/${debateId}/continue`, { user_input: userInput }).then(res => res.data);
}

// ============ 严谨分析 API ============

export interface RigorousAnalysisRequest {
  案件名称: string;
  原告?: string;
  被告?: string;
  案由?: string;
  诉讼金额?: string;
  案件描述?: string;
  我方证据?: string;
  对方名称?: string;
  对方类型?: string;
  对方证据?: string;
  对方攻击策略?: string;
  对方弱点?: string;
  分析阶段?: string;
  分析深度?: string;
}

export interface RigorousAnalysisProgress {
  analysis_id: string;
  status: 'not_found' | 'started' | 'completed';
  steps: Array<{
    name: string;
    status: 'pending' | 'in_progress' | 'completed';
    data: Record<string, unknown>;
  }>;
  unknown_info: string[];
  confirmed_facts: string[];
  speculations: string[];
  recommendations: string[];
  result?: {
    confirmed_facts: string[];
    speculations: string[];
    recommendations: string[];
    legal_analysis: string;
    opponent_analysis: string;
  };
  started_at: string;
  completed_at?: string;
}

/**
 * 启动严谨分析
 */
export async function startRigorousAnalysis(caseId: string, data: RigorousAnalysisRequest): Promise<{ analysis_id: string; status: string; unknown_info: string[]; message: string }> {
  return axiosInstance.post(`/api/adversarial/case/${caseId}/evidence-based-analysis`, data).then(res => res.data);
}

/**
 * 获取严谨分析进度
 */
export async function getRigorousAnalysisProgress(analysisId: string): Promise<RigorousAnalysisProgress> {
  return axiosInstance.get(`/api/adversarial/progress/${analysisId}`).then(res => res.data);
}

// ============ 完整分析 API ============

export interface FullAnalysisRequest {
  分析阶段?: string;
  对手名称?: string;
  对手类型?: string;
  我方证据?: string;
  对方证据?: string;
}

export interface FullAnalysisResponse {
  analysis_id: number;
  full_report: string;
}

/**
 * 生成完整对抗性分析草稿
 * 注意：这是一个同步API调用，会等待LLM完成
 * 设置了5分钟超时，防止浏览器超时
 */
export async function generateFullAnalysis(
  caseId: string, 
  data?: FullAnalysisRequest,
  timeout: number = 300000 // 5分钟超时
): Promise<FullAnalysisResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await axiosInstance.post(
      `/api/adversarial/case/${caseId}/full-analysis`, 
      data || {},
      { signal: controller.signal }
    );
    clearTimeout(timeoutId);
    return response.data;
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    if (error instanceof Error && (error.name === 'AbortError' || error.message.includes('canceled'))) {
      throw new Error('分析超时（超过5分钟），建议使用"后台分析"功能');
    }
    throw error;
  }
}

// ============ 对抗性分析列表与详情 API ============

export interface AdversarialAnalysisItem {
  id: number;
  case_id: number;
  title: string;
  analysis_phase: string;
  opponent_name?: string;
  opponent_type?: string;
  opponent_strength?: string;
  is_current: boolean;
  created_at: string;
  updated_at: string;
  // 分析内容字段
  我方优势?: string;
  我方弱点?: string;
  对方优势?: string;
  对方弱点?: string;
  对方可能行动?: string;
  对方证据预测?: string;
  对方攻击角度?: string;
  证据矩阵摘要?: string;
  可能情景?: string;
  情景概率?: Record<string, number>;
  总体策略?: string;
  立即行动?: string;
  应急预案?: string;
  风险评估?: string;
  风险缓解?: string;
}

/**
 * 获取对抗性分析详情
 */
export async function getAdversarialAnalysisDetail(analysisId: number): Promise<AdversarialAnalysisItem> {
  return axiosInstance.get(`/api/adversarial/${analysisId}`).then(res => res.data);
}

/**
 * 更新对抗性分析
 */
export async function updateAdversarialAnalysis(analysisId: number, data: Partial<AdversarialAnalysisItem>): Promise<AdversarialAnalysisItem> {
  return axiosInstance.put(`/api/adversarial/${analysisId}`, data).then(res => res.data);
}
