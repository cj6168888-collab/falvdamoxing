/**
 * 流式 AI 分析
 * 
 * 设计理念：
 * 1. 不限制算力 - 后端可以调用任意次 LLM 请求
 * 2. 不限制字数 - 流式输出，直到分析完成
 * 3. 全量证据综合分析 - 自动分块处理，不受上下文窗口限制
 * 4. 实时呈现 - SSE 流式推送到前端
 * 5. 持久化 - 分析结果自动保存到数据库
 * 
 * 工作流程：
 * 1. 前端提交分析请求（case_id + analysis_type + options）
 * 2. 后端创建分析任务，返回 task_id
 * 3. 前端建立 SSE 连接到 /api/streaming-analysis/{task_id}/stream
 * 4. 后端分阶段分析：
 *    - 阶段1：案件概览理解
 *    - 阶段2：全量证据逐个分析
 *    - 阶段3：证据交叉验证
 *    - 阶段4：法律适用分析
 *    - 阶段5：策略建议生成
 *    - 阶段6：风险评估
 *    - 阶段7：综合报告
 * 5. 每个阶段完成后通过 SSE 推送进度和内容
 * 6. 分析完成后推送最终结果
 */

import { API_BASE_URL, TOKEN_STORAGE_KEY } from '@/lib/api-config';
import axiosInstance from '@/api/client';

export interface AnalysisChunk {
  type: 'progress' | 'content' | 'stage_complete' | 'error' | 'complete';
  stage?: string;
  stageIndex?: number;
  totalStages?: number;
  content?: string;
  progress?: number;
  error?: string;
  taskId?: string;
}

export interface AnalysisRequest {
  caseId: string;
  analysisType: 'full' | 'evidence' | 'strategy' | 'risk' | 'custom';
  customPrompt?: string;
  options?: {
    depth?: 'quick' | 'standard' | 'deep' | 'exhaustive';
    includeEvidenceAnalysis?: boolean;
    includeLegalResearch?: boolean;
    includeStrategy?: boolean;
    includeRiskAssessment?: boolean;
  };
}

/**
 * 创建分析任务
 */
export async function createAnalysisTask(request: AnalysisRequest): Promise<{ task_id: string }> {
  return axiosInstance.post('/api/streaming-analysis/create', {
    case_id: parseInt(request.caseId),
    analysis_type: request.analysisType,
    custom_prompt: request.customPrompt,
    options: request.options,
  }).then(res => res.data);
}

/**
 * 启动分析任务执行
 */
export async function startAnalysisTask(taskId: string): Promise<void> {
  await axiosInstance.post(`/api/streaming-analysis/${taskId}/start`);
}

/**
 * 建立 SSE 流式连接
 * 返回一个 ReadableStream 用于读取分析结果
 */
export function createAnalysisStream(taskId: string): ReadableStream<AnalysisChunk> {
  const baseUrl = API_BASE_URL.replace(/\/$/, '');
  const url = `${baseUrl}/api/streaming-analysis/${taskId}/stream`;
  const token = typeof localStorage === 'undefined' ? null : localStorage.getItem(TOKEN_STORAGE_KEY);

  return new ReadableStream({
    async start(controller) {
      try {
        const response = await fetch(url, {
          headers: {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });

        if (!response.ok) {
          throw new Error(`SSE 连接失败: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('无法读取响应流');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        let isReading = true;

        while (isReading) {
          const { done, value } = await reader.read();
          if (done) {
            isReading = false;
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          
          // 解析 SSE 格式: data: {...}\n\n
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 保留最后一个不完整的行

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                controller.enqueue(data as AnalysisChunk);
                
                // 分析完成或出错时关闭流
                if (data.type === 'complete' || data.type === 'error') {
                  controller.close();
                  return;
                }
              } catch {
                // 忽略解析错误
              }
            }
          }
        }

        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });
}

/**
 * 使用流式分析
 * 返回一个异步迭代器，逐个产出分析结果
 */
export async function* streamAnalysis(taskId: string): AsyncGenerator<AnalysisChunk, void, unknown> {
  const stream = createAnalysisStream(taskId);
  const reader = stream.getReader();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield value;
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * 获取分析任务状态
 */
export async function getAnalysisStatus(taskId: string) {
  return axiosInstance.get(`/api/streaming-analysis/${taskId}/status`).then(res => res.data);
}

/**
 * 获取分析任务结果
 */
export async function getAnalysisResult(taskId: string) {
  return axiosInstance.get(`/api/streaming-analysis/${taskId}/result`).then(res => res.data);
}
