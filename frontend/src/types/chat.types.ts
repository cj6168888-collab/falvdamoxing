// 对话类型

export interface ChatMessage {
  id: string;
  caseId?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  intent?: string;
  clarificationNeeded?: boolean;
}

export interface Conversation {
  id: string;
  caseId?: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}
