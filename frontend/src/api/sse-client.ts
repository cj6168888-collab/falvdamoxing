import { API_BASE_URL } from '@/lib/api-config';

export interface SSEEvent {
  event: string;
  data: unknown;
}

type SSEPayload = Record<string, unknown>;

export interface SSECallbacks {
  onProgress?: (progress: number, message: string) => void;
  onSectionStart?: (sectionIndex: number, title: string) => void;
  onSectionContent?: (sectionIndex: number, title: string, content: string) => void;
  onSectionError?: (sectionIndex: number, title: string, error: string) => void;
  onComplete?: (reportId: string, title: string, reportType: string, totalSections: number, completedSections: number, createdAt: string) => void;
  onError?: (error: string) => void;
  onAbort?: () => void;
}

export function connectReportSSE(
  caseId: string,
  reportType: string,
  callbacks: SSECallbacks
): AbortController {
  const controller = new AbortController();
  const url = `${API_BASE_URL}/api/reports/generate-stream/${caseId}`;

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
    },
    body: JSON.stringify({ report_type: reportType }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
        callbacks.onError?.(errorText || `HTTP ${response.status}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError?.('无法读取响应流');
        return;
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
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = 'message';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            try {
              const data = JSON.parse(dataStr);
              handleSSEEvent(currentEvent, data, callbacks);
            } catch {
              // 忽略无效JSON
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name === 'AbortError') {
        callbacks.onAbort?.();
      } else {
        callbacks.onError?.(error.message || '连接失败');
      }
    });

  return controller;
}

function readString(data: SSEPayload, key: string): string {
  const value = data[key];
  return typeof value === 'string' ? value : String(value ?? '');
}

function readNumber(data: SSEPayload, key: string): number {
  const value = data[key];
  return typeof value === 'number' ? value : Number(value ?? 0);
}

function handleSSEEvent(event: string, data: SSEPayload, callbacks: SSECallbacks) {
  switch (event) {
    case 'progress':
      callbacks.onProgress?.(readNumber(data, 'progress'), readString(data, 'message'));
      break;
    case 'section_start':
      callbacks.onSectionStart?.(readNumber(data, 'section_index'), readString(data, 'title'));
      break;
    case 'section_content':
      callbacks.onSectionContent?.(readNumber(data, 'section_index'), readString(data, 'title'), readString(data, 'content'));
      break;
    case 'section_error':
      callbacks.onSectionError?.(readNumber(data, 'section_index'), readString(data, 'title'), readString(data, 'error'));
      break;
    case 'complete':
      callbacks.onComplete?.(
        readString(data, 'report_id'),
        readString(data, 'title'),
        readString(data, 'report_type'),
        readNumber(data, 'total_sections'),
        readNumber(data, 'completed_sections'),
        readString(data, 'created_at')
      );
      break;
    case 'error':
      callbacks.onError?.(readString(data, 'message') || readString(data, 'error'));
      break;
  }
}
