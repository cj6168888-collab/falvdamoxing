import { useState, useCallback } from 'react';
import type { 
  IntentResult, 
  IntentType, 
  ClarificationQuestion, 
  SuggestedAction,
  QuickAction 
} from '@/types/chat-v2.types';

// 意图识别API调用
async function recognizeIntent(message: string, context?: Record<string, unknown>): Promise<IntentResult> {
  const response = await fetch('/api/chat/intent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, context }),
  });
  
  if (!response.ok) {
    throw new Error('意图识别失败');
  }
  
  return response.json();
}

// 澄清确认API调用
async function submitClarification(
  clarificationId: string,
  answers: Record<string, string>
): Promise<IntentResult> {
  const response = await fetch('/api/chat/clarify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clarificationId, answers }),
  });
  
  return response.json();
}

// 预设快速操作
export const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'quick-evidence',
    label: '证据指导',
    icon: '📋',
    intent: 'evidence_help',
    description: '获取证据收集和准备建议',
  },
  {
    id: 'quick-document',
    label: '生成文书',
    icon: '📝',
    intent: 'document_generate',
    description: '生成起诉状、答辩状等文书',
  },
  {
    id: 'quick-deadline',
    label: '期限提醒',
    icon: '⏰',
    intent: 'deadline_query',
    description: '查询重要期限节点',
  },
  {
    id: 'quick-law',
    label: '法条检索',
    icon: '📖',
    intent: 'law_search',
    description: '检索相关法律条文',
  },
  {
    id: 'quick-strategy',
    label: '策略建议',
    icon: '🎯',
    intent: 'strategy_advice',
    description: '获取案件应对策略',
  },
  {
    id: 'quick-fee',
    label: '费用计算',
    icon: '💰',
    intent: 'fee_calculation',
    description: '计算诉讼费用',
  },
];

interface UseIntentRecognitionReturn {
  intent: IntentResult | null;
  isRecognizing: boolean;
  error: Error | null;
  recognizeIntent: (message: string) => Promise<void>;
  clearIntent: () => void;
}

export function useIntentRecognition(): UseIntentRecognitionReturn {
  const [intent, setIntent] = useState<IntentResult | null>(null);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const recognize = useCallback(async (message: string) => {
    setIsRecognizing(true);
    setError(null);
    
    try {
      const result = await recognizeIntent(message);
      setIntent(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('意图识别失败'));
      // 降级处理：基于关键词简单判断
      const fallbackIntent = simpleIntentDetection(message);
      setIntent(fallbackIntent);
    } finally {
      setIsRecognizing(false);
    }
  }, []);

  const clearIntent = useCallback(() => {
    setIntent(null);
    setError(null);
  }, []);

  return {
    intent,
    isRecognizing,
    error,
    recognizeIntent: recognize,
    clearIntent,
  };
}

// 简单的本地意图检测（降级方案）
function simpleIntentDetection(message: string): IntentResult {
  const lowerMessage = message.toLowerCase();
  
  // 关键词匹配
  const patterns: { intent: IntentType; keywords: string[]; confidence: number }[] = [
    { 
      intent: 'evidence_help', 
      keywords: ['证据', '材料', '证明', '收集', '准备'], 
      confidence: 0.8 
    },
    { 
      intent: 'document_generate', 
      keywords: ['生成', '起草', '写', '文书', '起诉状', '答辩状', '上诉状'], 
      confidence: 0.85 
    },
    { 
      intent: 'deadline_query', 
      keywords: ['期限', '截止', '什么时候', '几天', '多久'], 
      confidence: 0.75 
    },
    { 
      intent: 'law_search', 
      keywords: ['法律', '法条', '规定', '条文', '条款', '第', '条'], 
      confidence: 0.8 
    },
    { 
      intent: 'strategy_advice', 
      keywords: ['策略', '怎么', '如何', '建议', '办法', '方案'], 
      confidence: 0.7 
    },
    { 
      intent: 'case_info', 
      keywords: ['案件', '情况', '进度', '状态', '怎么样了'], 
      confidence: 0.75 
    },
    { 
      intent: 'fee_calculation', 
      keywords: ['费用', '多少钱', '诉讼费', '律师费', '成本'], 
      confidence: 0.8 
    },
  ];

  let bestMatch: { intent: IntentType; confidence: number } = { 
    intent: 'unknown', 
    confidence: 0 
  };

  for (const pattern of patterns) {
    const matches = pattern.keywords.filter(kw => lowerMessage.includes(kw)).length;
    if (matches > 0) {
      const confidence = pattern.confidence * Math.min(matches / 2, 1);
      if (confidence > bestMatch.confidence) {
        bestMatch = { intent: pattern.intent, confidence };
      }
    }
  }

  // 生成建议操作
  const suggestedActions: SuggestedAction[] = [];
  
  switch (bestMatch.intent) {
    case 'evidence_help':
      suggestedActions.push({
        id: 'action-evidence',
        type: 'search_evidence',
        label: '查看证据建议',
        description: '获取本案证据收集建议',
      });
      break;
    case 'document_generate':
      suggestedActions.push({
        id: 'action-document',
        type: 'generate_document',
        label: '生成文书',
        description: '选择文书类型开始生成',
      });
      break;
    case 'deadline_query':
      suggestedActions.push({
        id: 'action-deadline',
        type: 'show_deadline',
        label: '查看期限',
        description: '查看重要时间节点',
      });
      break;
    case 'law_search':
      suggestedActions.push({
        id: 'action-law',
        type: 'search_law',
        label: '检索法条',
        description: '搜索相关法律条文',
      });
      break;
  }

  return {
    intent: bestMatch.confidence > 0.5 ? bestMatch.intent : 'general_chat',
    confidence: bestMatch.confidence,
    entities: [],
    suggestions: [],
    requiresClarification: bestMatch.confidence < 0.6,
    suggestedActions,
    clarificationQuestions: bestMatch.confidence < 0.6 ? [
      {
        id: 'clarify-intent',
        question: '您想要我帮您做什么？',
        options: [
          { value: 'evidence', label: '帮我准备证据' },
          { value: 'document', label: '帮我生成文书' },
          { value: 'search', label: '查找相关法律' },
          { value: 'deadline', label: '查询重要期限' },
        ],
        required: true,
        context: '无法确定您的意图',
      },
    ] : undefined,
  };
}

interface UseClarificationReturn {
  currentQuestion: ClarificationQuestion | null;
  isClarifying: boolean;
  submitAnswer: (answer: string) => Promise<IntentResult | null>;
  skipClarification: () => void;
}

interface UseClarificationProps {
  questions: ClarificationQuestion[];
  onComplete: (result: IntentResult) => void;
  onSkip: () => void;
}

export function useClarification({
  questions,
  onComplete,
  onSkip,
}: UseClarificationProps): UseClarificationReturn {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isClarifying, setIsClarifying] = useState(false);

  const currentQuestion = questions[currentIndex] || null;

  const submitAnswer = useCallback(async (answer: string) => {
    const newAnswers = { ...answers, [currentQuestion?.id || '']: answer };
    setAnswers(newAnswers);
    
    // 如果还有下一个问题
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(i => i + 1);
      return null;
    }
    
    // 所有问题回答完毕，提交
    setIsClarifying(true);
    try {
      const result = await submitClarification('multi', newAnswers);
      onComplete(result);
      return result;
    } finally {
      setIsClarifying(false);
    }
  }, [answers, currentIndex, currentQuestion, questions, onComplete]);

  const skipClarification = useCallback(() => {
    setAnswers({});
    setCurrentIndex(0);
    onSkip();
  }, [onSkip]);

  return {
    currentQuestion,
    isClarifying,
    submitAnswer,
    skipClarification,
  };
}
