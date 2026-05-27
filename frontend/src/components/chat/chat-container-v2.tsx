import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useIntentRecognition, QUICK_ACTIONS } from '@/hooks/use-intent-recognition';
import { ClarificationPanel, IntentBadge, SuggestedActionsPanel, QuickActionsBar, GuidedModeIndicator } from './clarification-components';
import type { ChatMessage } from '@/types/chat.types';
import type { IntentResult, SuggestedAction } from '@/types/chat-v2.types';
import { useChatV2 } from '@/hooks/use-chat-v2';
import { 
  Send, 
  Sparkles, 
  RotateCcw, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  MessageCircle,
  Loader2
} from 'lucide-react';

interface ChatContainerV2Props {
  caseId: string;
  onSuggestedAction?: (action: SuggestedAction) => void;
}

export function ChatContainerV2({ caseId, onSuggestedAction }: ChatContainerV2Props) {
  const [message, setMessage] = useState('');
  const [chatMode, setChatMode] = useState<'normal' | 'guided' | 'clarification'>('normal');
  const [currentIntent, setCurrentIntent] = useState<IntentResult | null>(null);
  const [clarificationIndex, setClarificationIndex] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const { messages, addMessage, clearMessages, isLoading } = useChatV2(caseId);
  const { intent, isRecognizing, recognizeIntent, clearIntent } = useIntentRecognition();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Update current intent when recognition changes
  useEffect(() => {
    if (intent) {
      setCurrentIntent(intent);
      if (intent.requiresClarification && intent.clarificationQuestions?.length) {
        setChatMode('clarification');
      }
    }
  }, [intent]);

  const handleSend = useCallback(async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');

    // Add user message
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    });

    // Recognize intent (non-blocking)
    recognizeIntent(userMessage);

    // Send to API and get response
    try {
      // Response handled by useChatV2 hook
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [message, isLoading, addMessage, recognizeIntent]);

  const handleQuickAction = useCallback((action: typeof QUICK_ACTIONS[0]) => {
    setMessage(action.label);
    inputRef.current?.focus();
  }, []);

  const handleClarificationAnswer = useCallback((_answer: string) => {
    if (!currentIntent?.clarificationQuestions) return;

    const questions = currentIntent.clarificationQuestions;
    if (clarificationIndex < questions.length - 1) {
      // Move to next question
      setClarificationIndex(i => i + 1);
    } else {
      // All questions answered, switch to guided mode
      setChatMode('guided');
      setClarificationIndex(0);
      clearIntent();
    }
  }, [currentIntent, clarificationIndex, clearIntent]);

  const handleSkipClarification = useCallback(() => {
    setChatMode('guided');
    setClarificationIndex(0);
    clearIntent();
  }, [clearIntent]);

  const handleSuggestedAction = useCallback((action: SuggestedAction) => {
    onSuggestedAction?.(action);
  }, [onSuggestedAction]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[600px] border rounded-lg mx-auto max-w-6xl w-full px-4">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-primary" />
          <span className="font-medium">智能法律助手</span>
          <Badge variant="outline" className="text-xs">V2</Badge>
        </div>
        <div className="flex items-center gap-2">
          <GuidedModeIndicator mode={chatMode} onModeChange={setChatMode} />
          <Button variant="ghost" size="icon" onClick={() => clearMessages()} title="清空对话">
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {/* Welcome Message */}
          {messages.length === 0 && (
            <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium mb-2">您好！我是您的智能法律助手</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      我可以帮您：查询案件信息、准备证据、生成文书、检索法条、分析策略等。
                    </p>
                    
                    {/* Intent Display */}
                    {currentIntent && chatMode === 'normal' && (
                      <div className="mb-4">
                        <IntentBadge intent={currentIntent} onActionClick={handleSuggestedAction} />
                      </div>
                    )}

                    {/* Suggested Actions */}
                    {currentIntent?.suggestedActions && currentIntent.suggestedActions.length > 0 && (
                      <SuggestedActionsPanel
                        actions={currentIntent.suggestedActions}
                        onActionClick={handleSuggestedAction}
                        intent={currentIntent}
                      />
                    )}

                    {/* Quick Actions */}
                    {(!currentIntent || currentIntent.suggestedActions?.length === 0) && (
                      <div className="grid grid-cols-2 gap-2">
                        {QUICK_ACTIONS.slice(0, 4).map((action) => (
                          <button
                            key={action.id}
                            onClick={() => handleQuickAction(action)}
                            className="flex items-center gap-2 p-3 rounded-lg border bg-background hover:bg-muted/50 transition-colors text-left"
                          >
                            <span className="text-xl">{action.icon}</span>
                            <div>
                              <span className="text-sm font-medium">{action.label}</span>
                              <p className="text-xs text-muted-foreground">{action.description}</p>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Chat Messages */}
          {messages.map((msg) => (
            <ChatMessageBubble
              key={msg.id}
              message={msg}
            />
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-primary animate-pulse" />
              </div>
              <Card className="flex-1">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">正在分析您的问题...</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Clarification Panel */}
          {chatMode === 'clarification' && currentIntent?.clarificationQuestions && (
            <ClarificationPanel
              questions={currentIntent.clarificationQuestions}
              currentIndex={clarificationIndex}
              onAnswer={handleClarificationAnswer}
              onSkip={handleSkipClarification}
              suggestedActions={currentIntent.suggestedActions}
              intentResult={currentIntent}
            />
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Intent Recognition Indicator */}
      {isRecognizing && (
        <div className="px-4 py-2 border-t bg-muted/30">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Sparkles className="h-3 w-3 animate-pulse" />
            <span>正在识别意图...</span>
          </div>
        </div>
      )}

      {/* Quick Actions Bar */}
      <QuickActionsBar
        actions={QUICK_ACTIONS}
        onActionClick={handleQuickAction}
      />

      {/* Input Area */}
      <div className="flex gap-2 p-4 border-t bg-background">
        <Textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入您的问题，或点击快捷操作..."
          className="flex-1 min-h-[60px] max-h-[120px] max-w-4xl mx-auto w-full"
          disabled={isLoading}
        />
        <Button
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          size="icon"
          className="h-[60px] w-[60px] shrink-0"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}

// Chat Message Bubble Component
interface ChatMessageBubbleProps {
  message: ChatMessage;
}

function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-primary' : isAssistant ? 'bg-primary/20' : 'bg-muted'
      }`}>
        {isUser ? (
          <span className="text-xs text-primary-foreground font-medium">我</span>
        ) : (
          <Sparkles className="h-4 w-4 text-primary" />
        )}
      </div>

      {/* Message Content */}
      <Card className={`max-w-[80%] ${isUser ? 'bg-primary text-primary-foreground' : ''}`}>
        <CardContent className="p-4">
          {/* Intent Badge for Assistant */}
          {isAssistant && message.intent && (
            <div className="mb-2">
              <Badge variant="secondary" className="text-xs">
                {message.intent}
              </Badge>
            </div>
          )}

          {/* Message Text */}
          <div className="prose prose-sm max-w-none">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>

          {/* Actions for Assistant Messages */}
          {isAssistant && (
            <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
              <Button
                variant="ghost"
                size="sm"
                className="h-auto py-1 px-2 text-xs"
                onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
              >
                <ThumbsUp className={`h-3 w-3 mr-1 ${feedback === 'up' ? 'fill-current' : ''}`} />
                有帮助
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-auto py-1 px-2 text-xs"
                onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
              >
                <ThumbsDown className={`h-3 w-3 mr-1 ${feedback === 'down' ? 'fill-current' : ''}`} />
                不满意
              </Button>
              <Button variant="ghost" size="sm" className="h-auto py-1 px-2 text-xs">
                <Copy className="h-3 w-3 mr-1" />
                复制
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Timestamp */}
      <span className="text-xs text-muted-foreground flex-shrink-0 self-end">
        {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
}
