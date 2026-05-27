import { useState, useCallback, useEffect } from 'react';
import type { ChatMessage } from '@/types/chat.types';
import { useChatStore } from '@/stores/chat.store';

interface UseChatV2Return {
  messages: ChatMessage[];
  isLoading: boolean;
  error: Error | null;
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  regenerateResponse: () => Promise<void>;
}

export function useChatV2(caseId: string): UseChatV2Return {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastUserMessage, setLastUserMessage] = useState<string | null>(null);

  // Load messages from store on mount
  useEffect(() => {
    const storedMessages = useChatStore.getState().conversations[caseId];
    if (storedMessages) {
      setMessages(storedMessages);
    }
  }, [caseId]);

  // Save messages to store
  useEffect(() => {
    if (messages.length > 0) {
      useChatStore.getState().addMessage(caseId, messages[messages.length - 1]);
    }
  }, [messages, caseId]);

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    useChatStore.getState().clearConversation(caseId);
  }, [caseId]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    setIsLoading(true);
    setError(null);
    setLastUserMessage(content);

    try {
      // Call the API
      const response = await fetch('/api/chat/v2', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          caseId, 
          message: content,
          history: messages.slice(-10), // Send last 10 messages for context
        }),
      });

      if (!response.ok) {
        throw new Error('发送消息失败');
      }

      const data = await response.json();

      // Add assistant response
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: data.content || data.message || '',
        timestamp: new Date().toISOString(),
        intent: data.intent,
        clarificationNeeded: data.clarificationNeeded,
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error('发送消息失败'));
      
      // Add error message
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，请稍后再试。',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  }, [caseId, messages, addMessage]);

  const regenerateResponse = useCallback(async () => {
    if (!lastUserMessage) return;

    // Remove last assistant message
    setMessages(prev => prev.slice(0, -1));
    
    // Resend the message
    await sendMessage(lastUserMessage);
  }, [lastUserMessage, sendMessage]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    addMessage,
    clearMessages,
    regenerateResponse,
  };
}

// Streaming Chat Hook
interface UseStreamingChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: Error | null;
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
}

export function useStreamingChat(caseId: string): UseStreamingChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    useChatStore.getState().clearConversation(caseId);
  }, [caseId]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMessage);

    try {
      // Create placeholder for streaming response
      const assistantMessageId = (Date.now() + 1).toString();
      
      // Start streaming
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          caseId, 
          message: content,
        }),
      });

      if (!response.ok) {
        throw new Error('发送消息失败');
      }

      // Handle SSE streaming
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      if (reader) {
        let isDone = false;
        while (!isDone) {
          const { done, value } = await reader.read();
          isDone = done;
          if (done) break;

          const chunk = decoder.decode(value);
          fullContent += chunk;
        }
      }

      // Add complete assistant message
      addMessage({
        id: assistantMessageId,
        role: 'assistant',
        content: fullContent,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error('发送消息失败'));
    } finally {
      setIsLoading(false);
    }
  }, [caseId, addMessage]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    addMessage,
    clearMessages,
  };
}
