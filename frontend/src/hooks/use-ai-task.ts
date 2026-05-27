import { useCallback } from 'react';
import { useTaskStore, pollTaskStatus } from '@/stores/task.store';
import axiosInstance from '@/api/client';
import { toast } from 'sonner';

const generateId = (): string => crypto.randomUUID().slice(0, 12);

interface UseAITaskOptions {
  /** 任务类型 */
  type: string;
  /** 案件 ID */
  caseId: string;
  /** 任务标题 */
  title: string;
  /** 任务完成后的回调 */
  onComplete?: (result: unknown) => void;
  /** 任务失败后的回调 */
  onError?: (error: string) => void;
  /** 是否自动启动 */
  autoStart?: boolean;
}

/**
 * 异步 AI 任务 Hook
 * 提交任务后立即返回，后台轮询状态，用户可自由切换页面
 */
export function useAITask({
  type,
  caseId,
  title,
  onComplete,
  onError,
}: UseAITaskOptions) {
  const addTask = useTaskStore((s) => s.addTask);
  const updateTask = useTaskStore((s) => s.updateTask);

  const execute = useCallback(async (params: Record<string, unknown> = {}) => {
    const taskId = generateId();

    // 1. 注册到 Store
    addTask({
      id: taskId,
      type,
      caseId,
      title,
      result: undefined,
    });

    try {
      // 2. 创建后端任务
      await axiosInstance.post('/api/ai-tasks/create', {
        type,
        case_id: parseInt(caseId),
        title,
        params,
      });

      // 3. 启动执行
      await axiosInstance.post(`/api/ai-tasks/${taskId}/execute`);

      // 4. 开始轮询
      pollTaskStatus(taskId, (data) => {
        updateTask(taskId, {
          status: data.status,
          progress: data.progress,
          message: data.message,
          result: data.result,
          error: data.error,
          completedAt: data.status === 'completed' || data.status === 'failed' ? Date.now() : undefined,
        });

        if (data.status === 'completed') {
          toast.success(`${title} 已完成`);
          onComplete?.(data.result);
        } else if (data.status === 'failed') {
          const errorMessage = data.error || '任务执行失败';
          toast.error(`${title} 失败: ${errorMessage}`);
          onError?.(errorMessage);
        }
      });

      return taskId;
    } catch (err) {
      const errorMsg = getRequestErrorMessage(err, '任务创建失败');
      updateTask(taskId, {
        status: 'failed',
        error: errorMsg,
        message: errorMsg,
        completedAt: Date.now(),
      });
      toast.error(errorMsg);
      onError?.(errorMsg);
      return taskId;
    }
  }, [type, caseId, title, onComplete, onError, addTask, updateTask]);

  return { execute };
}

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || fallback;
  }
  return fallback;
}
