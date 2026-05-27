import { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useSendMessage } from '@/hooks/use-chat';
import { useChatStore } from '@/stores/chat.store';
import { Loader2, Bot, User, Sparkles } from 'lucide-react';

const CHAT_STEPS = [
  '正在理解您的问题...',
  '正在检索相关法律知识...',
  '正在分析案件关联...',
  '正在组织回答...',
  '正在进行深度分析...',
];

interface ChatContainerProps { caseId: string; }

export function ChatContainer({ caseId }: ChatContainerProps) {
  const [message, setMessage] = useState('');
  const [chatStep, setChatStep] = useState(0);
  const [chatProgress, setChatProgress] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const send = useSendMessage(caseId);
  const messages = useChatStore((state) => state.conversations[caseId] || []);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!send.isPending) {
      setChatStep(0);
      setChatProgress(0);
      setElapsedTime(0);
      return;
    }
    setChatStep(0);
    setChatProgress(0);
    setElapsedTime(0);

    const stepInterval = setInterval(() => {
      setChatStep((prev) => Math.min(prev + 1, CHAT_STEPS.length - 1));
    }, 10000);

    const progressInterval = setInterval(() => {
      setChatProgress((prev) => {
        const next = prev + (prev < 20 ? 2 : prev < 50 ? 1 : prev < 80 ? 0.5 : 0.2);
        return Math.min(next, 95);
      });
    }, 500);

    const elapsedInterval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
      clearInterval(elapsedInterval);
    };
  }, [send.isPending]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}分${s}秒`;
  };

  const handleSend = useCallback(() => {
    if (!message.trim()) return;

    const userMsg = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    console.log('[Chat] Sending message:', message.trim());
    console.log('[Chat] Case ID:', caseId);

    // Add user message to store immediately
    useChatStore.getState().addMessage(caseId, userMsg);

    // Clear input immediately
    setMessage('');

    // Send to backend
    send.mutate(message.trim());
  }, [message, caseId, send]);

  return (
    <div className="flex flex-col h-[600px] mx-auto max-w-6xl w-full px-4">
      <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <Card className="max-w-2xl">
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">您好！我是您的法律助手。请描述您的法律问题，我将基于全案信息进行深度分析。</p>
            </CardContent>
          </Card>
        )}
        {messages.map((msg) => (
          <Card key={msg.id} className={`max-w-2xl ${msg.role === 'user' ? 'ml-auto bg-blue-50' : 'mr-auto'}`}>
            <CardContent className="p-3">
              <div className="flex items-start gap-2">
                {msg.role === 'assistant' ? <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" /> : <User className="h-4 w-4 mt-0.5 flex-shrink-0" />}
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              </div>
            </CardContent>
          </Card>
        ))}
        {send.isPending && (
          <Card className="mr-auto max-w-2xl border-primary/20 bg-primary/5">
            <CardContent className="p-3">
              <div className="flex items-center gap-2 text-sm">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-primary font-medium">{CHAT_STEPS[chatStep]}</span>
              </div>
              <Progress value={chatProgress} className="mt-2 h-1" />
              <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <Sparkles className="h-3 w-3" />
                <span>已分析 {formatTime(elapsedTime)}，AI 正在进行深度法律分析...</span>
              </div>
            </CardContent>
          </Card>
        )}
        <div ref={messagesEndRef} />
      </CardContent>
      <div className="flex gap-2 p-4 border-t bg-background">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="输入您的问题，AI 将进行全量深度分析..."
          className="flex-1 max-w-4xl mx-auto w-full"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <Button onClick={handleSend} disabled={send.isPending} className="shrink-0">
          {send.isPending ? '深度分析中...' : '发送'}
        </Button>
      </div>
    </div>
  );
}
