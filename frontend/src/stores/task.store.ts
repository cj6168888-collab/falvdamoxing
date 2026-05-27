import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axiosInstance from '@/api/client';

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AITask {
  id: string;
  type: string;
  title: string;
  caseId: string;
  status: TaskStatus;
  progress: number;
  message: string;
  result?: unknown;
  error?: string;
  createdAt: number;
  completedAt?: number;
}

interface TaskStatusResponse {
  status: TaskStatus;
  progress: number;
  message?: string;
  result?: unknown;
  error?: string;
}

interface TaskStore {
  tasks: AITask[];
  addTask: (task: Omit<AITask, 'createdAt' | 'status' | 'progress' | 'message'>) => void;
  updateTask: (id: string, updates: Partial<AITask>) => void;
  removeTask: (id: string) => void;
  getTask: (id: string) => AITask | undefined;
  getActiveTasks: () => AITask[];
  getCompletedTasks: () => AITask[];
  getTasksByCase: (caseId: string) => AITask[];
  clearCompleted: () => void;
}

export const useTaskStore = create<TaskStore>()(
  persist(
    (set, get) => ({
      tasks: [],

      addTask: (task) => set((state) => ({
        tasks: [
          {
            ...task,
            status: 'pending',
            progress: 0,
            message: '任务已提交，等待处理...',
            createdAt: Date.now(),
          },
          ...state.tasks,
        ],
      })),

      updateTask: (id, updates) => set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === id ? { ...t, ...updates } : t
        ),
      })),

      removeTask: (id) => set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
      })),

      getTask: (id) => get().tasks.find((t) => t.id === id),

  getActiveTasks: () => get().tasks.filter((t) => t.status === 'pending' || t.status === 'running'),

  getCompletedTasks: () => get().tasks.filter((t) => t.status === 'completed'),

  getFailedTasks: () => get().tasks.filter((t) => t.status === 'failed'),

      getTasksByCase: (caseId) => get().tasks.filter((t) => t.caseId === caseId),

      clearCompleted: () => set((state) => ({
        tasks: state.tasks.filter((t) => t.status !== 'completed'),
      })),
    }),
    {
      name: 'ai-tasks-storage',
      partialize: (state) => ({
        tasks: state.tasks.filter((t) => t.status !== 'running' && t.status !== 'pending'),
      }),
    }
  )
);

/**
 * 轮询后端任务状态
 * 支持检测长时间无进度变化的任务
 */
export async function pollTaskStatus(
  taskId: string, 
  onUpdate: (data: TaskStatusResponse) => void,
  onStuck?: (elapsedSeconds: number) => void
): Promise<void> {
  const maxRetries = 600; // 增加最大重试次数到10分钟(600 * 1秒)
  const stuckThresholdSeconds = 120; // 2分钟无进度变化认为任务卡住
  let retries = 0;
  let lastProgress = -1;
  let lastProgressUpdateTime = Date.now();
  let stuckAlertShown = false;

  return new Promise((resolve) => {
    const poll = async () => {
      try {
        const res = await axiosInstance.get<TaskStatusResponse>(`/api/ai-tasks/${taskId}`);
        const data = res.data;
        onUpdate(data);

        // 检测进度是否变化
        if (data.progress !== lastProgress) {
          lastProgress = data.progress;
          lastProgressUpdateTime = Date.now();
          stuckAlertShown = false;
        }

        // 检测任务是否卡住（进度超过阈值时间没有变化，且任务仍在运行）
        const elapsedSeconds = Math.floor((Date.now() - lastProgressUpdateTime) / 1000);
        if (
          data.status === 'running' && 
          elapsedSeconds > stuckThresholdSeconds && 
          !stuckAlertShown
        ) {
          stuckAlertShown = true;
          console.warn(`[Task] 任务 ${taskId} 似乎卡住了，已 ${elapsedSeconds} 秒无进度变化`);
          onStuck?.(elapsedSeconds);
        }

        if (data.status === 'completed' || data.status === 'failed') {
          resolve();
          return;
        }

        retries++;
        if (retries < maxRetries) {
          setTimeout(poll, 1000); // 轮询间隔改为1秒
        } else {
          console.warn(`[Task] 任务 ${taskId} 轮询超时，已重试 ${maxRetries} 次`);
          resolve();
        }
      } catch {
        retries++;
        if (retries < maxRetries) {
          setTimeout(poll, 2000); // 网络错误时延长间隔
        } else {
          resolve();
        }
      }
    };

    setTimeout(poll, 1000);
  });
}
